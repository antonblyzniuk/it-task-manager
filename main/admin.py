from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from main.models import Position, Task, TaskType, Worker


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position", "role")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info", {"fields": ("position", "role")}
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional Info", {"fields": ("first_name", "last_name", "position", "role")}
        ),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "name", "deadline", "is_completed", "priority", "task_type", "created_by", "created_at"
    ]
    list_filter = ["task_type", "priority", "is_completed"]
    search_fields = ["name", "description"]
    raw_id_fields = ["created_by"]


admin.site.unregister(Group)
