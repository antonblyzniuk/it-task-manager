from django.urls import include, path

from main import views

project_urlpatterns = [
    path("", views.ProjectDetailView.as_view(), name="project-detail"),
    path("settings/", views.ProjectSettingsView.as_view(), name="project-settings"),
    path("delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
    path("invite/", views.project_invite_view, name="project-invite"),
    path("invite/regenerate/", views.project_regenerate_key_view, name="project-regen-key"),
    path("members/", views.project_members_view, name="project-members"),
    path("members/<int:worker_pk>/remove/", views.project_remove_member_view, name="project-remove-member"),
    path("members/<int:worker_pk>/set-role/", views.project_set_member_role_view, name="project-set-role"),
    path("leave/", views.project_leave_view, name="project-leave"),

    # Tasks
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

    # Positions
    path("positions/", views.PositionListView.as_view(), name="position-list"),
    path("positions/create/", views.PositionCreateView.as_view(), name="position-create"),
    path("positions/<int:pk>/update/", views.PositionUpdateView.as_view(), name="position-update"),
    path("positions/<int:pk>/delete/", views.PositionDeleteView.as_view(), name="position-delete"),

    # Task types
    path("task-types/", views.TaskTypeListView.as_view(), name="task-type-list"),
    path("task-types/create/", views.TaskTypeCreateView.as_view(), name="task-type-create"),
    path("task-types/<int:pk>/update/", views.TaskTypeUpdateView.as_view(), name="task-type-update"),
    path("task-types/<int:pk>/delete/", views.TaskTypeDeleteView.as_view(), name="task-type-delete"),

    # Project members / team
    path("workers/", views.ProjectWorkerListView.as_view(), name="project-worker-list"),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("admin-register/", views.admin_register_view, name="admin-register"),

    # Global worker routes
    path("workers/", views.WorkerListView.as_view(), name="worker-list"),
    path("workers/create/", views.WorkerCreateView.as_view(), name="worker-create"),
    path("workers/create-admin/", views.AdminWorkerCreateView.as_view(), name="worker-create-admin"),
    path("workers/<int:pk>/detail/", views.worker_detail_view, name="worker-detail"),
    path("workers/<int:pk>/update/", views.WorkerUpdateView.as_view(), name="worker-update"),
    path("workers/<int:pk>/delete/", views.WorkerDeleteView.as_view(), name="worker-delete"),

    # Projects
    path("projects/", views.project_list_view, name="project-list"),
    path("projects/create/", views.project_create_view, name="project-create"),
    path("projects/join/", views.join_project_view, name="project-join"),
    path("projects/<int:project_pk>/", include(project_urlpatterns)),
]

app_name = "main"
