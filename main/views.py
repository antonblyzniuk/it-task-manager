import hmac
from typing import Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import generic
from django.views.decorators.http import require_POST

from main.forms import (
    AdminRegistrationForm,
    TaskForm,
    TaskSearchForm,
    WorkerCreationForm,
    WorkerPositionUpdateForm,
    WorkerSearchForm,
)
from main.models import Position, Task, TaskType, Worker


def index(request: HttpRequest) -> HttpResponse:
    context = {
        "num_of_workers": Worker.objects.all().count(),
        "num_of_tasks": Task.objects.all().count(),
        "num_of_positions": Position.objects.all().count()
    }
    return render(request, "main/index.html", context=context)


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
            worker = Worker(username=form.cleaned_data["username"], is_staff=True, is_superuser=True)
            worker.set_password(form.cleaned_data["password"])
            worker.save()
            return redirect("login")

    return render(request, "main/admin_register.html", {"form": form})


class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    queryset = Position.objects.prefetch_related("workers")
    paginate_by = 13


class PositionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("main:position-list")


class PositionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("main:position-list")


class PositionDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Position
    template_name = "main/position_confirm_delete.html"
    success_url = reverse_lazy("main:position-list")


class TaskTypeListView(LoginRequiredMixin, generic.ListView):
    model = TaskType
    paginate_by = 13
    queryset = TaskType.objects.prefetch_related("tasks")
    template_name = "main/task_type_list.html"
    context_object_name = "task_type_list"


class TaskTypeCreateView(LoginRequiredMixin, generic.CreateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("main:task-type-list")
    template_name = "main/task_type_form.html"


class TaskTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("main:task-type-list")
    template_name = "main/task_type_form.html"


class TaskTypeDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = TaskType
    template_name = "main/task_type_confirm_delete.html"
    success_url = reverse_lazy("main:task-type-list")


class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    paginate_by = 13

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super(WorkerListView, self).get_context_data(**kwargs)
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


class WorkerUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
    form_class = WorkerPositionUpdateForm


class WorkerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Worker
    success_url = reverse_lazy("main:worker-list")
    template_name = "main/worker_confirm_delete.html"


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    paginate_by = 15

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super(TaskListView, self).get_context_data(**kwargs)
        name_or_priority = self.request.GET.get("name_or_priority", "")
        context["search_form"] = TaskSearchForm(
            initial={"name_or_priority": name_or_priority}
        )
        context["today"] = now()
        return context
    
    def get_queryset(self) -> QuerySet[Any]:
        queryset = Task.objects.select_related("task_type")
        form = TaskSearchForm(self.request.GET)
        if form.is_valid():
            search_term = form.cleaned_data["name_or_priority"]
            return queryset.filter(
                Q(name__icontains=search_term) |
                Q(priority__icontains=search_term)
                )
        return queryset


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("main:task-list")


# class TaskDetailView(LoginRequiredMixin, generic.DetailView):
#     model = Task


@login_required
def task_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task.objects.prefetch_related("assignees"), pk=pk)
    assignees = task.assignees.all()

    context = {
        "task": task,
        "assignees": assignees,
        "today": now(),
    }
    return render(request, "main/task_detail.html", context=context)


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm


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


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    template_name = "main/task_confirm_delete.html"
    success_url = reverse_lazy("main:task-list")
