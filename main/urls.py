from django.urls import path

from main import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin-register/", views.admin_register_view, name="admin-register"),

    path("positions/", views.PositionListView.as_view(), name="position-list"),
    path("positions/create/", views.PositionCreateView.as_view(), name="position-create"),
    path("positions/<int:pk>/update/", views.PositionUpdateView.as_view(), name="position-update"),
    path("positions/<int:pk>/delete/", views.PositionDeleteView.as_view(), name="position-delete"),

    path("task-types/", views.TaskTypeListView.as_view(), name="task-type-list"),
    path("task-types/create/", views.TaskTypeCreateView.as_view(), name="task-type-create"),
    path(
        "task-types/<int:pk>/update/",
        views.TaskTypeUpdateView.as_view(),
        name="task-type-update",
    ),
    path(
        "task-types/<int:pk>/delete/",
        views.TaskTypeDeleteView.as_view(),
        name="task-type-delete",
    ),

    path("workers/", views.WorkerListView.as_view(), name="worker-list"),
    path("workers/create/", views.WorkerCreateView.as_view(), name="worker-create"),
    path("workers/<int:pk>/detail/", views.worker_detail_view, name="worker-detail"),
    path("workers/<int:pk>/update/", views.WorkerUpdateView.as_view(), name="worker-update"),
    path("workers/<int:pk>/delete/", views.WorkerDeleteView.as_view(), name="worker-delete"),

    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/my/", views.MyTaskListView.as_view(), name="my-tasks"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/detail/", views.task_detail_view, name="task-detail"),
    path("tasks/<int:pk>/update/", views.TaskUpdateView.as_view(), name="task-update"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    path("tasks/<int:pk>/complete/", views.task_complete_view, name="task-complete"),
    path("tasks/<int:pk>/assign/me/", views.task_assign_me_view, name="task-assign-me"),
    path(
        "tasks/<int:task_pk>/unassign/<int:worker_pk>/worker/",
        views.task_unassign_worker_view,
        name="task-unassign-worker",
    ),
]

app_name = "main"
