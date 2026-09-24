from datetime import datetime
from api.core.exceptions import EmptyTaskUpdateError, TaskNotFoundError
from api.repositories.interfaces import TaskRepository
from api.domain.task import Task
from api.domain.enums import TaskPriority, TaskStatus

class TaskService:
    def __init__(self, task_repository: TaskRepository) -> None:
        self._task_repository = task_repository

    def create_task(
        self, *,
        title: str,
        content: str,
        deadline: datetime,
        priority: TaskPriority,
        status: TaskStatus,
        user_id: int
    ) -> Task:
        task = Task(
            title=title,
            content=content,
            deadline=deadline,
            priority=priority,
            status=status,
            user_id=user_id)
        return self._task_repository.add(task=task)

    def get_task(self, *, task_id: int, user_id: int) -> Task:
        task = self._task_repository.get_by_id_for_user(task_id=task_id, user_id=user_id)
        if task is None:
            raise TaskNotFoundError("Task not found.")
        return task

    def list_tasks(self, *, user_id: int) -> list[Task]:
        return self._task_repository.list_by_user(user_id=user_id)

    def list_expired_tasks(self, *, user_id: int, now: datetime) -> list[Task]:
        return self._task_repository.list_expired(user_id=user_id, now=now)

    def delete_task(self, *, task_id: int, user_id: int) -> None:
        return self._task_repository.delete(task_id=task_id, user_id=user_id)

    def update_task(
        self,
        *,
        task_id: int,
        user_id: int,
        title: str | None = None,
        content: str | None = None,
        deadline: datetime | None = None,
        priority: TaskPriority | None = None,
        status: TaskStatus | None = None
    ) -> Task:

        if (
            title is None
            and content is None
            and deadline is None
            and priority is None
            and status is None
        ):
            raise EmptyTaskUpdateError("At least one field must be provided.")

        task = self.get_task(task_id=task_id, user_id=user_id)

        if title is not None:
            task.update_title(title=title)
        if content is not None:
            task.update_content(content=content)
        if deadline is not None:
            task.reschedule(deadline=deadline)
        if priority is not None:
            task.change_priority(priority=priority)
        if status is not None:
            task.change_status(status=status)

        self._task_repository.update(task=task)
        return task