from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from main.models import OneTimeInvite, Position, Project, ProjectMembership, Task, TaskType, Worker


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "created_at"]
    search_fields = ["name"]
    list_filter = ["project"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "created_at"]
    search_fields = ["name"]
    list_filter = ["project"]


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("role",)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("first_name", "last_name", "role")}),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "deadline", "is_completed", "priority", "task_type", "created_by", "created_at"]
    list_filter = ["project", "task_type", "priority", "is_completed"]
    search_fields = ["name", "description"]
    raw_id_fields = ["created_by"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["secret_key"]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ["worker", "project", "role", "position", "joined_at"]
    list_filter = ["role", "project"]
    search_fields = ["worker__username", "project__name"]


@admin.register(OneTimeInvite)
class OneTimeInviteAdmin(admin.ModelAdmin):
    list_display = ["project", "position", "created_by", "created_at"]
    list_filter = ["project"]


admin.site.unregister(Group)
