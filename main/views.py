import hmac
from typing import Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import generic
from django.views.decorators.http import require_POST

from main.forms import (
    AdminRegistrationForm,
    AdminWorkerCreationForm,
    TaskFilterForm,
    TaskForm,
    WorkerCreationForm,
    WorkerPositionUpdateForm,
    WorkerSearchForm,
)
from main.models import Position, Task, TaskType, Worker

# ---------------------------------------------------------------------------
# Permission mixins
# ---------------------------------------------------------------------------

class AdminRequiredMixin(UserPassesTestMixin):
    """Only ADMIN role or superuser."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.is_admin


class ManagerRequiredMixin(UserPassesTestMixin):
    """MANAGER, ADMIN, or superuser."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.is_manager


class TaskOwnerOrAdminMixin(UserPassesTestMixin):
    """Task creator, any assignee, or admin can modify the task."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        task = self.get_object()
        return task.created_by == user or user in task.assignees.all()


class SelfOrAdminMixin(UserPassesTestMixin):
    """A worker can only modify their own profile; admins can modify anyone's."""
    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return self.get_object().pk == user.pk


# ---------------------------------------------------------------------------
# General views
# ---------------------------------------------------------------------------

def index(request: HttpRequest) -> HttpResponse:
    today = now().date()
    num_open_tasks = Task.objects.filter(is_completed=False).count()
    num_of_workers = Worker.objects.count()
    context = {
        "num_of_workers": num_of_workers,
        "num_of_tasks": Task.objects.count(),
        "num_of_positions": Position.objects.count(),
        "num_of_task_types": TaskType.objects.count(),
        "num_completed_tasks": Task.objects.filter(is_completed=True).count(),
        "num_open_tasks": num_open_tasks,
        "num_overdue_tasks": Task.objects.filter(is_completed=False, deadline__lt=today).count(),
        "num_urgent_tasks": Task.objects.filter(priority="urgent", is_completed=False).count(),
        "num_high_tasks": Task.objects.filter(priority="high", is_completed=False).count(),
        "num_admins": Worker.objects.filter(role="admin").count(),
        "num_managers": Worker.objects.filter(role="manager").count(),
        "num_developers": Worker.objects.filter(role="developer").count(),
        "recent_tasks": Task.objects.select_related("task_type", "created_by")
                            .prefetch_related("assignees")
                            .order_by("-id")[:5],
        "completion_rate": round(
            Task.objects.filter(is_completed=True).count() /
            max(Task.objects.count(), 1) * 100
        ),
        "num_medium_low_tasks": Task.objects.filter(
            is_completed=False, priority__in=["medium", "low"]
        ).count(),
        "open_tasks_max": max(num_open_tasks, 1),
        "workers_max": max(num_of_workers, 1),
        "now": now(),
    }
    return render(request, "main/index.html", context=context)


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
# Position views
# ---------------------------------------------------------------------------

class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    queryset = Position.objects.prefetch_related("workers")
    paginate_by = 13


class PositionCreateView(AdminRequiredMixin, generic.CreateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("main:position-list")


class PositionUpdateView(AdminRequiredMixin, generic.UpdateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("main:position-list")


class PositionDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = Position
    template_name = "main/position_confirm_delete.html"
    success_url = reverse_lazy("main:position-list")


# ---------------------------------------------------------------------------
# TaskType views
# ---------------------------------------------------------------------------

class TaskTypeListView(LoginRequiredMixin, generic.ListView):
    model = TaskType
    paginate_by = 13
    queryset = TaskType.objects.prefetch_related("tasks")
    template_name = "main/task_type_list.html"
    context_object_name = "task_type_list"


class TaskTypeCreateView(AdminRequiredMixin, generic.CreateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("main:task-type-list")
    template_name = "main/task_type_form.html"


class TaskTypeUpdateView(AdminRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("main:task-type-list")
    template_name = "main/task_type_form.html"


class TaskTypeDeleteView(AdminRequiredMixin, generic.DeleteView):
    model = TaskType
    template_name = "main/task_type_confirm_delete.html"
    success_url = reverse_lazy("main:task-type-list")


# ---------------------------------------------------------------------------
# Worker views
# ---------------------------------------------------------------------------

class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    paginate_by = 13

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        username_or_position_name = self.request.GET.get("username_or_position_name", "")
        context["search_form"] = WorkerSearchForm(
            initial={"username_or_position_name": username_or_position_name}
        )
        return context

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Worker.objects.select_related("position").prefetch_related("tasks")
        form = WorkerSearchForm(self.request.GET)
        if form.is_valid():
            search_term = form.cleaned_data["username_or_position_name"]
            return queryset.filter(
                Q(username__icontains=search_term) |
                Q(position__name__icontains=search_term)
            )
        return queryset


@login_required
def worker_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    worker = get_object_or_404(Worker.objects.prefetch_related("tasks"), pk=pk)
    assigned_tasks = worker.tasks.all()
    assigned_tasks_count = assigned_tasks.count()
    completed_tasks_count = assigned_tasks.filter(is_completed=True).count()

    context = {
        "worker": worker,
        "assigned_tasks": assigned_tasks,
        "assigned_tasks_count": assigned_tasks_count,
        "completed_tasks_count": completed_tasks_count,
        "today": now(),
    }

    return render(request, "main/worker_detail.html", context=context)


class WorkerCreateView(generic.CreateView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
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
# Task views
# ---------------------------------------------------------------------------

class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "main/task_list.html"
    context_object_name = "task_list"

    def get_queryset(self) -> QuerySet[Any]:
        qs = Task.objects.select_related("task_type").prefetch_related("assignees")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        today = now()
        qs = self.object_list
        context["tasks_todo"] = (
            qs.filter(is_completed=False, deadline__gte=today).order_by("deadline")
        )
        context["tasks_overdue"] = (
            qs.filter(is_completed=False, deadline__lt=today).order_by("deadline")
        )
        context["tasks_done"] = qs.filter(is_completed=True).order_by("-updated_at")
        context["filter_form"] = TaskFilterForm(self.request.GET)
        context["today"] = today
        return context


class MyTaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "main/my_task_list.html"
    context_object_name = "task_list"
    paginate_by = 15

    def get_queryset(self) -> QuerySet[Any]:
        return (
            Task.objects
            .filter(assignees=self.request.user)
            .select_related("task_type")
            .order_by("is_completed", "deadline")
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["today"] = now()
        return context


class TaskCreateView(ManagerRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("main:task-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@login_required
def task_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    qs = Task.objects.select_related("created_by").prefetch_related("assignees")
    task = get_object_or_404(qs, pk=pk)
    assignees = task.assignees.all()

    context = {
        "task": task,
        "assignees": assignees,
        "today": now(),
    }
    return render(request, "main/task_detail.html", context=context)


class TaskUpdateView(TaskOwnerOrAdminMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm


class TaskDeleteView(TaskOwnerOrAdminMixin, generic.DeleteView):
    model = Task
    template_name = "main/task_confirm_delete.html"
    success_url = reverse_lazy("main:task-list")


@login_required
@require_POST
def task_complete_view(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = True
    task.save()
    return redirect("main:task-detail", pk=pk)


@login_required
@require_POST
def task_assign_me_view(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task.objects.prefetch_related("assignees"), pk=pk)
    if request.user not in task.assignees.all():
        task.assignees.add(request.user)
        task.save()
    return redirect("main:task-detail", pk=pk)


@login_required
@require_POST
def task_unassign_worker_view(
        request: HttpRequest,
        task_pk: int,
        worker_pk: int
) -> HttpResponse:
    task = get_object_or_404(Task.objects.prefetch_related("assignees"), pk=task_pk)
    worker = task.assignees.filter(id=worker_pk).first()
    if worker:
        task.assignees.remove(worker)
        task.save()
    return redirect("main:task-detail", pk=task_pk)
