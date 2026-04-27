from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from main.models import Project, ProjectMembership, Task, TaskType, Worker


class PublicViewsTest(TestCase):
    def test_index_view_redirects_to_login(self):
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 302)

    def test_login_view_public(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_get_worker_create_view_public(self):
        response = self.client.get(reverse("main:worker-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/worker_form.html")

    def test_post_worker_create_view_valid_data_public(self):
        form_data = {
            "username": "test_worker",
            "password1": "Strongpassword123%",
            "password2": "Strongpassword123%",
            "email": "test@example.com",
        }
        response = self.client.post(reverse("main:worker-create"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Worker.objects.filter(username="test_worker").exists())

    def test_post_worker_create_view_invalid_data_public(self):
        form_data = {
            "username": "wrong",
            "password1": "123",
            "password2": "123",
        }
        response = self.client.post(reverse("main:worker-create"), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Worker.objects.filter(username="wrong").exists())


class PrivateViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass", role=Worker.Role.DEVELOPER
        )
        self.manager = get_user_model().objects.create_user(
            username="testmanager", password="testpass", role=Worker.Role.MANAGER
        )
        self.admin = get_user_model().objects.create_user(
            username="testadmin", password="testpass", role=Worker.Role.ADMIN
        )
        self.project = Project.objects.create(name="Test Project", owner=self.admin)
        ProjectMembership.objects.create(
            project=self.project, worker=self.admin, role=ProjectMembership.Role.OWNER
        )
        ProjectMembership.objects.create(
            project=self.project, worker=self.manager, role=ProjectMembership.Role.ADMIN
        )
        ProjectMembership.objects.create(
            project=self.project, worker=self.user, role=ProjectMembership.Role.MEMBER
        )
        self.client.force_login(self.user)

    # --- Position views ---

    def test_position_list_view(self):
        response = self.client.get(
            reverse("main:position-list", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_position_create_view_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("main:position-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_position_create_view_developer_denied(self):
        response = self.client.get(
            reverse("main:position-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_position_update_view_admin(self):
        from main.models import Position
        self.client.force_login(self.admin)
        pos = Position.objects.create(name="Manager", project=self.project)
        response = self.client.get(
            reverse("main:position-update", kwargs={"project_pk": self.project.pk, "pk": pos.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_position_update_view_developer_denied(self):
        from main.models import Position
        pos = Position.objects.create(name="Manager", project=self.project)
        response = self.client.get(
            reverse("main:position-update", kwargs={"project_pk": self.project.pk, "pk": pos.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_position_delete_view_admin(self):
        from main.models import Position
        self.client.force_login(self.admin)
        pos = Position.objects.create(name="Developer", project=self.project)
        response = self.client.get(
            reverse("main:position-delete", kwargs={"project_pk": self.project.pk, "pk": pos.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_position_delete_view_developer_denied(self):
        from main.models import Position
        pos = Position.objects.create(name="Developer", project=self.project)
        response = self.client.get(
            reverse("main:position-delete", kwargs={"project_pk": self.project.pk, "pk": pos.id})
        )
        self.assertEqual(response.status_code, 403)

    # --- TaskType views ---

    def test_task_type_list_view(self):
        response = self.client.get(
            reverse("main:task-type-list", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_type_create_view_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("main:task-type-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_type_create_view_developer_denied(self):
        response = self.client.get(
            reverse("main:task-type-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_task_type_update_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Bug", project=self.project)
        response = self.client.get(
            reverse("main:task-type-update", kwargs={"project_pk": self.project.pk, "pk": task_type.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_type_update_view_developer_denied(self):
        task_type = TaskType.objects.create(name="Bug", project=self.project)
        response = self.client.get(
            reverse("main:task-type-update", kwargs={"project_pk": self.project.pk, "pk": task_type.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_task_type_delete_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Feature", project=self.project)
        response = self.client.get(
            reverse("main:task-type-delete", kwargs={"project_pk": self.project.pk, "pk": task_type.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_type_delete_view_developer_denied(self):
        task_type = TaskType.objects.create(name="Feature", project=self.project)
        response = self.client.get(
            reverse("main:task-type-delete", kwargs={"project_pk": self.project.pk, "pk": task_type.id})
        )
        self.assertEqual(response.status_code, 403)

    # --- Worker views ---

    def test_worker_list_view(self):
        response = self.client.get(reverse("main:worker-list"))
        self.assertEqual(response.status_code, 200)

    def test_worker_detail_view(self):
        worker = Worker.objects.create_user(username="worker1", password="pass")
        response = self.client.get(reverse("main:worker-detail", args=[worker.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_update_view_self(self):
        response = self.client.get(reverse("main:worker-update", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_update_view_other_denied(self):
        other = Worker.objects.create_user(username="other", password="pass")
        response = self.client.get(reverse("main:worker-update", args=[other.id]))
        self.assertEqual(response.status_code, 403)

    def test_worker_update_view_admin_other_denied(self):
        self.client.force_login(self.admin)
        other = Worker.objects.create_user(username="other2", password="pass")
        response = self.client.get(reverse("main:worker-update", args=[other.id]))
        self.assertEqual(response.status_code, 403)

    def test_worker_delete_view_admin(self):
        self.client.force_login(self.admin)
        worker = Worker.objects.create_user(username="worker3", password="pass")
        response = self.client.get(reverse("main:worker-delete", args=[worker.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_delete_view_developer_denied(self):
        other = Worker.objects.create_user(username="worker4", password="pass")
        response = self.client.get(reverse("main:worker-delete", args=[other.id]))
        self.assertEqual(response.status_code, 403)

    # --- Task views ---

    def test_task_list_view(self):
        response = self.client.get(
            reverse("main:task-list", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_list_view_with_filters(self):
        task_type = TaskType.objects.create(name="Filter", project=self.project)
        Task.objects.create(
            name="Filtered", deadline="2025-12-12", priority="high",
            task_type=task_type, project=self.project,
        )
        url = (
            reverse("main:task-list", kwargs={"project_pk": self.project.pk})
            + "?priority=high&is_completed=false"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_my_tasks_view(self):
        response = self.client.get(
            reverse("main:my-tasks", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_my_tasks_view_only_shows_assigned_tasks(self):
        task_type = TaskType.objects.create(name="Mine", project=self.project)
        my_task = Task.objects.create(
            name="My Task", deadline="2025-12-12", task_type=task_type, project=self.project,
        )
        other_task = Task.objects.create(
            name="Other Task", deadline="2025-12-12", task_type=task_type, project=self.project,
        )
        my_task.assignees.add(self.user)
        response = self.client.get(
            reverse("main:my-tasks", kwargs={"project_pk": self.project.pk})
        )
        self.assertIn(my_task, response.context["task_list"])
        self.assertNotIn(other_task, response.context["task_list"])

    def test_task_create_view_project_admin(self):
        self.client.force_login(self.manager)
        TaskType.objects.create(name="CreateTest", project=self.project)
        response = self.client.get(
            reverse("main:task-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_create_view_developer_denied(self):
        response = self.client.get(
            reverse("main:task-create", kwargs={"project_pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_task_create_sets_created_by(self):
        self.client.force_login(self.manager)
        task_type = TaskType.objects.create(name="CreatedBy", project=self.project)
        response = self.client.post(
            reverse("main:task-create", kwargs={"project_pk": self.project.pk}),
            {
                "name": "Created Task",
                "description": "Test",
                "deadline": "2025-12-12T12:00",
                "priority": "medium",
                "task_type": task_type.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(name="Created Task")
        self.assertEqual(task.created_by, self.manager)

    def test_task_detail_view(self):
        task_type = TaskType.objects.create(name="Fix", project=self.project)
        task = Task.objects.create(
            name="Fix bug", deadline="2025-12-12", priority="high",
            task_type=task_type, project=self.project,
        )
        response = self.client.get(
            reverse("main:task-detail", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_project_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Build", project=self.project)
        task = Task.objects.create(
            name="Build system", deadline="2025-12-12", priority="medium",
            task_type=task_type, project=self.project,
        )
        response = self.client.get(
            reverse("main:task-update", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_creator(self):
        self.client.force_login(self.manager)
        task_type = TaskType.objects.create(name="Build2", project=self.project)
        task = Task.objects.create(
            name="Owner Task", deadline="2025-12-12", task_type=task_type,
            project=self.project, created_by=self.manager,
        )
        response = self.client.get(
            reverse("main:task-update", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_member_not_creator_denied(self):
        task_type = TaskType.objects.create(name="Unauthorized", project=self.project)
        task = Task.objects.create(
            name="Not mine", deadline="2025-12-12", task_type=task_type, project=self.project,
        )
        response = self.client.get(
            reverse("main:task-update", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_task_delete_view_project_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Cleanup", project=self.project)
        task = Task.objects.create(
            name="Clean code", deadline="2025-12-12", priority="low",
            task_type=task_type, project=self.project,
        )
        response = self.client.get(
            reverse("main:task-delete", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_delete_view_member_not_creator_denied(self):
        task_type = TaskType.objects.create(name="DeleteTest", project=self.project)
        task = Task.objects.create(
            name="Not mine either", deadline="2025-12-12", task_type=task_type, project=self.project,
        )
        response = self.client.get(
            reverse("main:task-delete", kwargs={"project_pk": self.project.pk, "pk": task.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_task_complete_view(self):
        task_type = TaskType.objects.create(name="Check", project=self.project)
        task = Task.objects.create(
            name="Check logs", deadline="2025-12-12", priority="high",
            task_type=task_type, project=self.project,
        )
        url = reverse("main:task-complete", kwargs={"project_pk": self.project.pk, "pk": task.id})
        response = self.client.post(url)
        expected = reverse(
            "main:task-detail", kwargs={"project_pk": self.project.pk, "pk": task.id}
        )
        self.assertRedirects(response, expected)

    def test_task_assign_me_view(self):
        task_type = TaskType.objects.create(name="Write", project=self.project)
        task = Task.objects.create(
            name="Write report", deadline="2025-12-12", priority="high",
            task_type=task_type, project=self.project,
        )
        url = reverse("main:task-assign-me", kwargs={"project_pk": self.project.pk, "pk": task.id})
        response = self.client.post(url)
        expected = reverse(
            "main:task-detail", kwargs={"project_pk": self.project.pk, "pk": task.id}
        )
        self.assertRedirects(response, expected)

    def test_task_unassign_worker_view(self):
        task_type = TaskType.objects.create(name="Unassign", project=self.project)
        task = Task.objects.create(
            name="Unassign task", deadline="2025-12-12", priority="low",
            task_type=task_type, project=self.project,
        )
        task.assignees.add(self.user)
        url = reverse(
            "main:task-unassign-worker",
            kwargs={
                "project_pk": self.project.pk,
                "task_pk": task.id,
                "worker_pk": self.user.id,
            },
        )
        response = self.client.post(url)
        expected = reverse(
            "main:task-detail", kwargs={"project_pk": self.project.pk, "pk": task.id}
        )
        self.assertRedirects(response, expected)
