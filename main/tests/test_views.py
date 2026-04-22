from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from main.models import Position, Task, TaskType, Worker


class PublicViewsTest(TestCase):
    def test_index_view_public(self):
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/index.html")
        self.assertEqual(
            response.context.get("num_of_workers"),
            Worker.objects.all().count()
        )
        self.assertEqual(
            response.context.get("num_of_tasks"),
            Task.objects.all().count()
        )
        self.assertEqual(
            response.context.get("num_of_positions"),
            Position.objects.all().count()
        )

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
        self.client.force_login(self.user)

    # --- Position views ---

    def test_position_list_view(self):
        response = self.client.get(reverse("main:position-list"))
        self.assertEqual(response.status_code, 200)

    def test_position_create_view_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("main:position-create"))
        self.assertEqual(response.status_code, 200)

    def test_position_create_view_developer_denied(self):
        response = self.client.get(reverse("main:position-create"))
        self.assertEqual(response.status_code, 403)

    def test_position_update_view_admin(self):
        self.client.force_login(self.admin)
        pos = Position.objects.create(name="Manager")
        response = self.client.get(reverse("main:position-update", args=[pos.id]))
        self.assertEqual(response.status_code, 200)

    def test_position_update_view_developer_denied(self):
        pos = Position.objects.create(name="Manager")
        response = self.client.get(reverse("main:position-update", args=[pos.id]))
        self.assertEqual(response.status_code, 403)

    def test_position_delete_view_admin(self):
        self.client.force_login(self.admin)
        pos = Position.objects.create(name="Developer")
        response = self.client.get(reverse("main:position-delete", args=[pos.id]))
        self.assertEqual(response.status_code, 200)

    def test_position_delete_view_developer_denied(self):
        pos = Position.objects.create(name="Developer")
        response = self.client.get(reverse("main:position-delete", args=[pos.id]))
        self.assertEqual(response.status_code, 403)

    # --- TaskType views ---

    def test_task_type_list_view(self):
        response = self.client.get(reverse("main:task-type-list"))
        self.assertEqual(response.status_code, 200)

    def test_task_type_create_view_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("main:task-type-create"))
        self.assertEqual(response.status_code, 200)

    def test_task_type_create_view_developer_denied(self):
        response = self.client.get(reverse("main:task-type-create"))
        self.assertEqual(response.status_code, 403)

    def test_task_type_update_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Bug")
        response = self.client.get(reverse("main:task-type-update", args=[task_type.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_type_update_view_developer_denied(self):
        task_type = TaskType.objects.create(name="Bug")
        response = self.client.get(reverse("main:task-type-update", args=[task_type.id]))
        self.assertEqual(response.status_code, 403)

    def test_task_type_delete_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Feature")
        response = self.client.get(reverse("main:task-type-delete", args=[task_type.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_type_delete_view_developer_denied(self):
        task_type = TaskType.objects.create(name="Feature")
        response = self.client.get(reverse("main:task-type-delete", args=[task_type.id]))
        self.assertEqual(response.status_code, 403)

    # --- Worker views ---

    def test_worker_list_view(self):
        response = self.client.get(reverse("main:worker-list"))
        self.assertEqual(response.status_code, 200)

    def test_worker_detail_view(self):
        position = Position.objects.create(name="Tester")
        worker = Worker.objects.create_user(
            username="worker1", password="pass", position=position
        )
        response = self.client.get(reverse("main:worker-detail", args=[worker.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_update_view_self(self):
        response = self.client.get(reverse("main:worker-update", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_update_view_other_denied(self):
        other = Worker.objects.create_user(username="other", password="pass")
        response = self.client.get(reverse("main:worker-update", args=[other.id]))
        self.assertEqual(response.status_code, 403)

    def test_worker_update_view_admin(self):
        self.client.force_login(self.admin)
        other = Worker.objects.create_user(username="other2", password="pass")
        response = self.client.get(reverse("main:worker-update", args=[other.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_delete_view_admin(self):
        self.client.force_login(self.admin)
        position = Position.objects.create(name="Leader")
        worker = Worker.objects.create_user(
            username="worker3", password="pass", position=position
        )
        response = self.client.get(reverse("main:worker-delete", args=[worker.id]))
        self.assertEqual(response.status_code, 200)

    def test_worker_delete_view_developer_denied(self):
        other = Worker.objects.create_user(username="worker4", password="pass")
        response = self.client.get(reverse("main:worker-delete", args=[other.id]))
        self.assertEqual(response.status_code, 403)

    # --- Task views ---

    def test_task_list_view(self):
        response = self.client.get(reverse("main:task-list"))
        self.assertEqual(response.status_code, 200)

    def test_task_list_view_with_filters(self):
        task_type = TaskType.objects.create(name="Filter")
        Task.objects.create(
            name="Filtered", deadline="2025-12-12", priority="high", task_type=task_type
        )
        url = reverse("main:task-list") + "?priority=high&is_completed=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_my_tasks_view(self):
        response = self.client.get(reverse("main:my-tasks"))
        self.assertEqual(response.status_code, 200)

    def test_my_tasks_view_only_shows_assigned_tasks(self):
        task_type = TaskType.objects.create(name="Mine")
        my_task = Task.objects.create(
            name="My Task", deadline="2025-12-12", task_type=task_type
        )
        other_task = Task.objects.create(
            name="Other Task", deadline="2025-12-12", task_type=task_type
        )
        my_task.assignees.add(self.user)
        response = self.client.get(reverse("main:my-tasks"))
        self.assertIn(my_task, response.context["task_list"])
        self.assertNotIn(other_task, response.context["task_list"])

    def test_task_create_view_manager(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("main:task-create"))
        self.assertEqual(response.status_code, 200)

    def test_task_create_view_developer_denied(self):
        response = self.client.get(reverse("main:task-create"))
        self.assertEqual(response.status_code, 403)

    def test_task_create_sets_created_by(self):
        self.client.force_login(self.manager)
        task_type = TaskType.objects.create(name="CreatedBy")
        response = self.client.post(reverse("main:task-create"), {
            "name": "Created Task",
            "description": "Test",
            "deadline": "2025-12-12T12:00",
            "priority": "medium",
            "task_type": task_type.id,
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(name="Created Task")
        self.assertEqual(task.created_by, self.manager)

    def test_task_detail_view(self):
        task_type = TaskType.objects.create(name="Fix")
        task = Task.objects.create(
            name="Fix bug", deadline="2025-12-12", priority="High", task_type=task_type
        )
        response = self.client.get(reverse("main:task-detail", args=[task.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Build")
        task = Task.objects.create(
            name="Build system",
            deadline="2025-12-12",
            priority="Medium",
            task_type=task_type,
        )
        response = self.client.get(reverse("main:task-update", args=[task.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_owner(self):
        self.client.force_login(self.manager)
        task_type = TaskType.objects.create(name="Build2")
        task = Task.objects.create(
            name="Owner Task",
            deadline="2025-12-12",
            task_type=task_type,
            created_by=self.manager,
        )
        response = self.client.get(reverse("main:task-update", args=[task.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_update_view_developer_not_owner_denied(self):
        task_type = TaskType.objects.create(name="Unauthorized")
        task = Task.objects.create(
            name="Not mine", deadline="2025-12-12", task_type=task_type
        )
        response = self.client.get(reverse("main:task-update", args=[task.id]))
        self.assertEqual(response.status_code, 403)

    def test_task_delete_view_admin(self):
        self.client.force_login(self.admin)
        task_type = TaskType.objects.create(name="Cleanup")
        task = Task.objects.create(
            name="Clean code",
            deadline="2025-12-12",
            priority="Low",
            task_type=task_type,
        )
        response = self.client.get(reverse("main:task-delete", args=[task.id]))
        self.assertEqual(response.status_code, 200)

    def test_task_delete_view_developer_not_owner_denied(self):
        task_type = TaskType.objects.create(name="DeleteTest")
        task = Task.objects.create(
            name="Not mine either", deadline="2025-12-12", task_type=task_type
        )
        response = self.client.get(reverse("main:task-delete", args=[task.id]))
        self.assertEqual(response.status_code, 403)

    def test_task_complete_view(self):
        task_type = TaskType.objects.create(name="Check")
        task = Task.objects.create(
            name="Check logs", deadline="2025-12-12", priority="High", task_type=task_type
        )
        response = self.client.post(reverse("main:task-complete", args=[task.id]))
        self.assertRedirects(response, reverse("main:task-detail", args=[task.id]))

    def test_task_assign_me_view(self):
        task_type = TaskType.objects.create(name="Write")
        task = Task.objects.create(
            name="Write report", deadline="2025-12-12", priority="High", task_type=task_type
        )
        response = self.client.post(reverse("main:task-assign-me", args=[task.id]))
        self.assertRedirects(response, reverse("main:task-detail", args=[task.id]))

    def test_task_unassign_worker_view(self):
        task_type = TaskType.objects.create(name="Unassign")
        task = Task.objects.create(
            name="Unassign task",
            deadline="2025-12-12",
            priority="Low",
            task_type=task_type,
        )
        task.assignees.add(self.user)
        response = self.client.post(
            reverse("main:task-unassign-worker", args=[task.id, self.user.id])
        )
        self.assertRedirects(response, reverse("main:task-detail", args=[task.id]))
