from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from main.models import Position, Task, TaskType, Worker


class ModelsStrTest(TestCase):

    def test_task_type_str(self):
        task_type = TaskType(name="test_task_type")
        self.assertEqual(str(task_type), task_type.name)

    def test_position_str(self):
        position = Position(name="test_position")
        self.assertEqual(str(position), position.name)

    def test_worker_str(self):
        worker = Worker(
            username="test_username",
            password="test_password",
            first_name="test_first_name",
            last_name="test_last_name",
            position=Position(name="test_position")
        )
        self.assertEqual(str(worker), f"{worker.username} ({worker.position})")

    def test_task_str(self):
        task = Task(
            name="test_task_name",
            description="test_task_description",
            deadline=now(),
            priority=Task.Priority.HIGH,
            task_type=TaskType(name="test_task_type")
        )
        expected = (
            f"{task.name}(type: {task.task_type}, deadline: {task.deadline}, "
            f"priority: {task.priority}, is_completed: {task.is_completed})"
        )
        self.assertEqual(str(task), expected)


class ModelsGetAbsoluteUrlTest(TestCase):

    def test_get_absolute_url_worker(self):
        worker = Worker.objects.create_user(
            username="test_username",
            password="test_password",
            first_name="test_first_name",
            last_name="test_last_name",
        )
        expected_url = reverse("main:worker-detail", args=[str(worker.id)])
        self.assertEqual(worker.get_absolute_url(), expected_url)

    def test_get_absolute_url_task(self):
        task_type = TaskType.objects.create(name="test_task_type")

        task = Task.objects.create(
            name="test_task_name",
            description="test_task_description",
            deadline=now(),
            priority=Task.Priority.HIGH,
            task_type=task_type
        )
        expected_url = reverse("main:task-detail", args=[str(task.id)])
        self.assertEqual(task.get_absolute_url(), expected_url)
