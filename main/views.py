import hmac
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views import generic
from django.views.decorators.http import require_POST

from main.forms import (
    AdminRegistrationForm,
    AdminWorkerCreationForm,
    JoinProjectForm,
    ProjectForm,
    TaskFilterForm,
    TaskForm,
    WorkerCreationForm,
    WorkerPositionUpdateForm,
    WorkerSearchForm,
)
from main.models import Position, Project, ProjectMembership, Task, TaskType, Worker


# ---------------------------------------------------------------------------
# Global permission mixins
# ---------------------------------------------------------------------------

class AdminRequiredMixin(UserPassesTestMixin):
    """Only global ADMIN role or superuser."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.is_admin


class SelfOrAdminMixin(UserPassesTestMixin):
    """A worker can only modify their own profile; global admins can modify anyone's."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return self.get_object().pk == user.pk


# ---------------------------------------------------------------------------
# Project permission mixins
# ---------------------------------------------------------------------------

class ProjectContextMixin:
    """
    Fetches the project from URL kwargs and loads the user's membership.
    Must appear AFTER LoginRequiredMixin in the MRO so it only runs for
    authenticated users (LoginRequiredMixin short-circuits first).
    """

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("project_pk"))
        try:
            self._membership = ProjectMembership.objects.get(
                project=self.project, worker=request.user
            )
            self._user_project_role = self._membership.role
        except ProjectMembership.DoesNotExist:
            self._membership = None
            self._user_project_role = None
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        ctx["user_project_role"] = self._user_project_role
        ctx["user_is_project_admin"] = self._user_project_role in ("admin", "owner")
        ctx["user_is_project_owner"] = self._user_project_role == "owner"
        return ctx


class ProjectMemberRequiredMixin(LoginRequiredMixin, ProjectContextMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        return self._user_project_role is not None


class ProjectAdminRequiredMixin(LoginRequiredMixin, ProjectContextMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        return self._user_project_role in ("admin", "owner")


class ProjectOwnerRequiredMixin(LoginRequiredMixin, ProjectContextMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        return self._user_project_role == "owner"


class ProjectTaskOwnerOrAdminMixin(LoginRequiredMixin, ProjectContextMixin, UserPassesTestMixin):
    """Task creator, any assignee, or project admin/owner may modify the task."""
    raise_exception = True

    def test_func(self) -> bool:
        if self._user_project_role in ("admin", "owner"):
            return True
        if self._user_project_role is None:
            return False
        task = self.get_object()
        user = self.request.user
        return task.created_by == user or user in task.assignees.all()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_project_membership(user, project_pk):
    """Returns (project, role_str | None). Raises 404 if the project does not exist."""
    project = get_object_or_404(Project, pk=project_pk)
    try:
        m = ProjectMembership.objects.get(project=project, worker=user)
        return project, m.role
    except ProjectMembership.DoesNotExist:
        return project, None


# ---------------------------------------------------------------------------
# General views
# ---------------------------------------------------------------------------

@login_required
def index(request: HttpRequest) -> HttpResponse:
    return redirect("main:project-list")


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "main/about.html")


def admin_register_view(request: HttpRequest) -> HttpResponse:
    from django.http import Http404
    secret_code = settings.ADMIN_SECRET_CODE
    if not secret_code:
        raise Http404

    form = AdminRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entered_code = form.cleaned_data["secret_code"]
        if not hmac.compare_digest(entered_code, secret_code):
            form.add_error("secret_code", "Invalid secret code.")
        elif Worker.objects.filter(username=form.cleaned_data["username"]).exists():
            form.add_error("username", "This username is already taken.")
        else:
            worker = Worker(
                username=form.cleaned_data["username"],
                is_staff=True,
                is_superuser=True,
                role=Worker.Role.ADMIN,
            )
            worker.set_password(form.cleaned_data["password"])
            worker.save()
            return redirect("login")

    return render(request, "main/admin_register.html", {"form": form})


# ---------------------------------------------------------------------------
# Project views
# ---------------------------------------------------------------------------

@login_required
def project_list_view(request: HttpRequest) -> HttpResponse:
    memberships = (
        ProjectMembership.objects
        .filter(worker=request.user)
        .select_related("project", "project__owner")
        .order_by("-project__updated_at")
    )
    return render(request, "main/project_list.html", {"memberships": memberships})


@login_required
def project_create_view(request: HttpRequest) -> HttpResponse:
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.secret_key = Project.generate_key()
        project.save()
        ProjectMembership.objects.create(
            project=project,
            worker=request.user,
            role=ProjectMembership.Role.OWNER,
        )
        return redirect("main:project-detail", project_pk=project.pk)
    return render(request, "main/project_form.html", {"form": form, "title": "Create Project"})


@login_required
def join_project_view(request: HttpRequest) -> HttpResponse:
    form = JoinProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        key = form.cleaned_data["secret_key"].strip()
        try:
            project = Project.objects.get(secret_key=key)
        except Project.DoesNotExist:
            form.add_error("secret_key", "No project found with this key.")
        else:
            ProjectMembership.objects.get_or_create(
                project=project,
                worker=request.user,
                defaults={"role": ProjectMembership.Role.MEMBER},
            )
            return redirect("main:project-detail", project_pk=project.pk)
    return render(request, "main/join_project.html", {"form": form})


class ProjectDetailView(ProjectMemberRequiredMixin, generic.TemplateView):
    template_name = "main/project_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        today = now().date()
        tasks = self.project.tasks
        total = tasks.count()
        num_open = tasks.filter(is_completed=False).count()
        ctx.update({
            "num_tasks": total,
            "num_completed_tasks": tasks.filter(is_completed=True).count(),
            "num_open_tasks": num_open,
            "num_overdue_tasks": tasks.filter(is_completed=False, deadline__lt=today).count(),
            "num_urgent_tasks": tasks.filter(priority="urgent", is_completed=False).count(),
            "num_high_tasks": tasks.filter(priority="high", is_completed=False).count(),
            "num_medium_low_tasks": tasks.filter(
                is_completed=False, priority__in=["medium", "low"]
            ).count(),
            "num_members": self.project.memberships.count(),
            "recent_tasks": tasks.select_related("task_type", "created_by").order_by("-id")[:5],
            "completion_rate": round(
                tasks.filter(is_completed=True).count() / max(total, 1) * 100
            ),
            "open_tasks_max": max(num_open, 1),
            "now": now(),
        })
        return ctx


class ProjectSettingsView(ProjectAdminRequiredMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "main/project_settings.html"

    def get_object(self, queryset=None):
        return self.project

    def get_success_url(self):
        return reverse("main:project-settings", kwargs={"project_pk": self.project.pk})


class ProjectDeleteView(ProjectOwnerRequiredMixin, generic.DeleteView):
    model = Project
    template_name = "main/project_confirm_delete.html"
    success_url = reverse_lazy("main:project-list")

    def get_object(self, queryset=None):
        return self.project


@login_required
def project_invite_view(request: HttpRequest, project_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role not in ("admin", "owner"):
        raise PermissionDenied
    return render(request, "main/project_invite.html", {
        "project": project,
        "user_project_role": role,
        "user_is_project_admin": True,
        "user_is_project_owner": role == "owner",
    })


@login_required
@require_POST
def project_regenerate_key_view(request: HttpRequest, project_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role != "owner":
        raise PermissionDenied
    project.secret_key = Project.generate_key()
    project.save(update_fields=["secret_key", "updated_at"])
    return redirect("main:project-invite", project_pk=project_pk)


@login_required
def project_members_view(request: HttpRequest, project_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    memberships = project.memberships.select_related("worker", "worker__position").all()
    return render(request, "main/project_members.html", {
        "project": project,
        "memberships": memberships,
        "user_project_role": role,
        "user_is_project_admin": role in ("admin", "owner"),
        "user_is_project_owner": role == "owner",
    })


@login_required
@require_POST
def project_remove_member_view(request: HttpRequest, project_pk: int, worker_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role not in ("admin", "owner"):
        raise PermissionDenied
    target = get_object_or_404(ProjectMembership, project=project, worker_id=worker_pk)
    if target.role == "owner":
        raise PermissionDenied
    if role == "admin" and target.role == "admin":
        raise PermissionDenied
    target.delete()
    return redirect("main:project-members", project_pk=project_pk)


@login_required
@require_POST
def project_set_member_role_view(request: HttpRequest, project_pk: int, worker_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role != "owner":
        raise PermissionDenied
    target = get_object_or_404(ProjectMembership, project=project, worker_id=worker_pk)
    if target.role == "owner":
        raise PermissionDenied
    new_role = request.POST.get("role")
    if new_role not in ("admin", "member"):
        raise PermissionDenied
    target.role = new_role
    target.save(update_fields=["role"])
    return redirect("main:project-members", project_pk=project_pk)


@login_required
@require_POST
def project_leave_view(request: HttpRequest, project_pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    if role == "owner":
        messages.error(
            request,
            "Project owner cannot leave. Delete the project or transfer ownership first.",
        )
        return redirect("main:project-detail", project_pk=project_pk)
    ProjectMembership.objects.filter(project=project, worker=request.user).delete()
    return redirect("main:project-list")


# ---------------------------------------------------------------------------
# Position views  (project-scoped)
# ---------------------------------------------------------------------------

class PositionListView(ProjectMemberRequiredMixin, generic.ListView):
    model = Position
    paginate_by = 13

    def get_queryset(self) -> QuerySet:
        return Position.objects.filter(project=self.project).prefetch_related("workers")


class PositionCreateView(ProjectAdminRequiredMixin, generic.CreateView):
    model = Position
    fields = ["name"]

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("main:position-list", kwargs={"project_pk": self.project.pk})


class PositionUpdateView(ProjectAdminRequiredMixin, generic.UpdateView):
    model = Position
    fields = ["name"]

    def get_queryset(self):
        return Position.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse("main:position-list", kwargs={"project_pk": self.project.pk})


class PositionDeleteView(ProjectAdminRequiredMixin, generic.DeleteView):
    model = Position
    template_name = "main/position_confirm_delete.html"

    def get_queryset(self):
        return Position.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse("main:position-list", kwargs={"project_pk": self.project.pk})


# ---------------------------------------------------------------------------
# TaskType views  (project-scoped)
# ---------------------------------------------------------------------------

class TaskTypeListView(ProjectMemberRequiredMixin, generic.ListView):
    model = TaskType
    paginate_by = 13
    template_name = "main/task_type_list.html"
    context_object_name = "task_type_list"

    def get_queryset(self) -> QuerySet:
        return TaskType.objects.filter(project=self.project).prefetch_related("tasks")


class TaskTypeCreateView(ProjectAdminRequiredMixin, generic.CreateView):
    model = TaskType
    fields = ["name"]
    template_name = "main/task_type_form.html"

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("main:task-type-list", kwargs={"project_pk": self.project.pk})


class TaskTypeUpdateView(ProjectAdminRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = ["name"]
    template_name = "main/task_type_form.html"

    def get_queryset(self):
        return TaskType.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse("main:task-type-list", kwargs={"project_pk": self.project.pk})


class TaskTypeDeleteView(ProjectAdminRequiredMixin, generic.DeleteView):
    model = TaskType
    template_name = "main/task_type_confirm_delete.html"

    def get_queryset(self):
        return TaskType.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse("main:task-type-list", kwargs={"project_pk": self.project.pk})


# ---------------------------------------------------------------------------
# Worker views
# ---------------------------------------------------------------------------

class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    paginate_by = 13

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["search_form"] = WorkerSearchForm(
            initial={"username_or_position_name": self.request.GET.get("username_or_position_name", "")}
        )
        return context

    def get_queryset(self) -> QuerySet:
        queryset = Worker.objects.select_related("position").prefetch_related("tasks")
        form = WorkerSearchForm(self.request.GET)
        if form.is_valid():
            search_term = form.cleaned_data["username_or_position_name"]
            return queryset.filter(
                Q(username__icontains=search_term) | Q(position__name__icontains=search_term)
            )
        return queryset


class ProjectWorkerListView(ProjectMemberRequiredMixin, generic.ListView):
    template_name = "main/project_worker_list.html"
    context_object_name = "memberships"
    paginate_by = 13

    def get_queryset(self) -> QuerySet:
        return (
            ProjectMembership.objects
            .filter(project=self.project)
            .select_related("worker", "worker__position")
            .order_by("role", "worker__username")
        )


@login_required
def worker_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    worker = get_object_or_404(Worker.objects.prefetch_related("tasks"), pk=pk)
    assigned_tasks = worker.tasks.select_related("task_type", "project").all()
    context = {
        "worker": worker,
        "assigned_tasks": assigned_tasks,
        "assigned_tasks_count": assigned_tasks.count(),
        "completed_tasks_count": assigned_tasks.filter(is_completed=True).count(),
        "today": now(),
    }
    return render(request, "main/worker_detail.html", context=context)


class WorkerCreateView(generic.CreateView):
    model = Worker
    success_url = reverse_lazy("main:project-list")
    form_class = WorkerCreationForm


class AdminWorkerCreateView(AdminRequiredMixin, generic.CreateView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
    form_class = AdminWorkerCreationForm


class WorkerUpdateView(SelfOrAdminMixin, generic.UpdateView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
    form_class = WorkerPositionUpdateForm


class WorkerDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
    template_name = "main/worker_confirm_delete.html"


# ---------------------------------------------------------------------------
# Task views  (project-scoped)
# ---------------------------------------------------------------------------

class TaskListView(ProjectMemberRequiredMixin, generic.ListView):
    model = Task
    template_name = "main/task_list.html"
    context_object_name = "task_list"

    def get_queryset(self) -> QuerySet:
        qs = (
            Task.objects.filter(project=self.project)
            .select_related("task_type")
            .prefetch_related("assignees")
        )
        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        priority = self.request.GET.get("priority", "")
        if priority:
            qs = qs.filter(priority=priority)
        is_completed = self.request.GET.get("is_completed", "")
        if is_completed == "true":
            qs = qs.filter(is_completed=True)
        elif is_completed == "false":
            qs = qs.filter(is_completed=False)
        task_type = self.request.GET.get("task_type", "")
        if task_type:
            qs = qs.filter(task_type_id=task_type)
        assignee = self.request.GET.get("assignee", "")
        if assignee:
            qs = qs.filter(assignees__id=assignee)
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        today = now()
        qs = self.object_list
        ctx["tasks_todo"] = qs.filter(is_completed=False, deadline__gte=today).order_by("deadline")
        ctx["tasks_overdue"] = qs.filter(is_completed=False, deadline__lt=today).order_by("deadline")
        ctx["tasks_done"] = qs.filter(is_completed=True).order_by("-updated_at")
        ctx["filter_form"] = TaskFilterForm(self.request.GET, project=self.project)
        ctx["today"] = today
        return ctx


class MyTaskListView(ProjectMemberRequiredMixin, generic.ListView):
    model = Task
    template_name = "main/my_task_list.html"
    context_object_name = "task_list"
    paginate_by = 15

    def get_queryset(self) -> QuerySet:
        return (
            Task.objects
            .filter(project=self.project, assignees=self.request.user)
            .select_related("task_type")
            .order_by("is_completed", "deadline")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = now()
        return ctx


class TaskCreateView(ProjectAdminRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm

    def get(self, request, *args, **kwargs):
        if not TaskType.objects.filter(project=self.project).exists():
            messages.warning(
                request,
                "Please add at least one task type before creating tasks.",
            )
            return redirect("main:task-type-create", project_pk=self.project.pk)
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "main:task-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.object.pk},
        )


@login_required
def task_detail_view(request: HttpRequest, project_pk: int, pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    qs = (
        Task.objects.filter(project=project)
        .select_related("created_by")
        .prefetch_related("assignees")
    )
    task = get_object_or_404(qs, pk=pk)
    return render(request, "main/task_detail.html", {
        "task": task,
        "assignees": task.assignees.all(),
        "today": now(),
        "project": project,
        "user_project_role": role,
        "user_is_project_admin": role in ("admin", "owner"),
        "user_is_project_owner": role == "owner",
    })


class TaskUpdateView(ProjectTaskOwnerOrAdminMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm

    def get_queryset(self):
        return Task.objects.filter(project=self.project)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def get_success_url(self):
        return reverse(
            "main:task-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.object.pk},
        )


class TaskDeleteView(ProjectTaskOwnerOrAdminMixin, generic.DeleteView):
    model = Task
    template_name = "main/task_confirm_delete.html"

    def get_queryset(self):
        return Task.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse("main:task-list", kwargs={"project_pk": self.project.pk})


@login_required
@require_POST
def task_complete_view(request: HttpRequest, project_pk: int, pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    task = get_object_or_404(Task, pk=pk, project=project)
    task.is_completed = True
    task.save()
    return redirect("main:task-detail", project_pk=project_pk, pk=pk)


@login_required
@require_POST
def task_assign_me_view(request: HttpRequest, project_pk: int, pk: int) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    task = get_object_or_404(Task.objects.prefetch_related("assignees"), pk=pk, project=project)
    if request.user not in task.assignees.all():
        task.assignees.add(request.user)
    return redirect("main:task-detail", project_pk=project_pk, pk=pk)


@login_required
@require_POST
def task_unassign_worker_view(
    request: HttpRequest,
    project_pk: int,
    task_pk: int,
    worker_pk: int,
) -> HttpResponse:
    project, role = _get_project_membership(request.user, project_pk)
    if role is None:
        raise PermissionDenied
    task = get_object_or_404(
        Task.objects.prefetch_related("assignees"), pk=task_pk, project=project
    )
    worker = task.assignees.filter(id=worker_pk).first()
    if worker:
        task.assignees.remove(worker)
    return redirect("main:task-detail", project_pk=project_pk, pk=task_pk)
