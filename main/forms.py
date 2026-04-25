from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from main.models import Project, Task, TaskType, Worker


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Project name"}),
            "description": forms.Textarea(attrs={
                "class": "form-control", "rows": 3, "placeholder": "Short description (optional)"
            }),
        }


class JoinProjectForm(forms.Form):
    secret_key = forms.CharField(
        max_length=64,
        label="Secret Key",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Paste the project secret key here",
        }),
    )


class WorkerCreationForm(UserCreationForm):
    class Meta:
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "position",
            "first_name",
            "last_name",
        )


class AdminWorkerCreationForm(WorkerCreationForm):
    role = forms.ChoiceField(
        choices=[
            (Worker.Role.DEVELOPER, "Developer"),
            (Worker.Role.MANAGER, "Manager"),
        ],
        initial=Worker.Role.DEVELOPER,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(WorkerCreationForm.Meta):
        fields = WorkerCreationForm.Meta.fields + ("role",)


class WorkerPositionUpdateForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["username", "first_name", "last_name", "position"]


class WorkerSearchForm(forms.Form):
    username_or_position_name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "Search by username or position..."})
    )


class TaskFilterForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "placeholder": "Search tasks...",
            "class": "form-control form-control-sm",
        }),
    )
    priority = forms.ChoiceField(
        choices=[("", "All priorities")] + list(Task.Priority.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    is_completed = forms.ChoiceField(
        choices=[("", "All status"), ("false", "Active"), ("true", "Completed")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    task_type = forms.ModelChoiceField(
        queryset=TaskType.objects.none(),
        required=False,
        empty_label="All types",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    assignee = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        empty_label="All assignees",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["task_type"].queryset = TaskType.objects.filter(project=project)
            self.fields["assignee"].queryset = (
                get_user_model().objects.filter(project_memberships__project=project).distinct()
            )
        else:
            self.fields["task_type"].queryset = TaskType.objects.all()
            self.fields["assignee"].queryset = get_user_model().objects.all()


class AdminRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "form-control", "placeholder": "Password (min 8 characters)"
        }),
    )
    secret_code = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Secret code"}),
    )


class TaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            "class": "form-control",
            "type": "datetime-local",
        }),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    assignees = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        required=False,
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["assignees"].queryset = (
                get_user_model().objects.filter(project_memberships__project=project).distinct()
            )
            self.fields["task_type"].queryset = TaskType.objects.filter(project=project)
        else:
            self.fields["assignees"].queryset = get_user_model().objects.all()
            self.fields["task_type"].queryset = TaskType.objects.all()

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "deadline",
            "priority",
            "task_type",
            "assignees",
            "is_completed",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "task_type": forms.Select(attrs={"class": "form-select"}),
            "is_completed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
