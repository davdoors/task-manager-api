"""Persist task entities using SQLAlchemy and SQLite."""

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.core.exceptions import TaskNotFoundError
from api.db.models import TaskModel
from api.domain.task import Task
from api.repositories.interfaces import TaskRepository


class SQLiteTaskRepository(TaskRepository):
    """Store and retrieve tasks within their owner's scope."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: TaskModel) -> Task:
        """Convert a database model into a domain entity."""
        return Task(
            task_id=model.id,
            title=model.title,
            content=model.content,
            deadline=model.deadline,
            status=model.status,
            priority=model.priority,
            user_id=model.user_id,
        )

    def add(self, *, task: Task) -> Task:
        """Persist a new task and return an entity with its generated ID."""
        if task.id is not None:
            raise ValueError("A new task must not already have an ID.")

        model = TaskModel(
            title=task.title,
            content=task.content,
            deadline=task.deadline,
            status=task.status,
            priority=task.priority,
            user_id=task.user_id,
        )

        try:
            self._session.add(model)
            self._session.flush()
            persisted_task = self._to_domain(model)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

        return persisted_task

    def get_by_id_for_user(
        self,
        *,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        """Return the task only when it belongs to the given user."""
        statement = select(TaskModel).where(
            TaskModel.id == task_id,
            TaskModel.user_id == user_id,
        )
        model = self._session.scalar(statement)

        return self._to_domain(model) if model is not None else None

    def list_by_user(self, *, user_id: int) -> list[Task]:
        """Return the user's tasks in a deterministic order."""
        statement = (
            select(TaskModel)
            .where(TaskModel.user_id == user_id)
            .order_by(TaskModel.id)
        )
        models = self._session.scalars(statement)

        return [self._to_domain(model) for model in models]

    def list_expired(
        self,
        *,
        user_id: int,
        now: datetime,
    ) -> list[Task]:
        """Return expired tasks regardless of their status."""
        statement = (
            select(TaskModel)
            .where(
                TaskModel.user_id == user_id,
                TaskModel.deadline < now,
            )
            .order_by(TaskModel.deadline, TaskModel.id)
        )
        models = self._session.scalars(statement)

        return [self._to_domain(model) for model in models]

    def update(self, *, task: Task) -> None:
        """Update an existing task without changing its owner."""
        if task.id is None:
            raise TaskNotFoundError("Task not found.")

        statement = (
            update(TaskModel)
            .where(
                TaskModel.id == task.id,
                TaskModel.user_id == task.user_id,
            )
            .values(
                title=task.title,
                content=task.content,
                deadline=task.deadline,
                status=task.status,
                priority=task.priority,
            )
        )

        try:
            result = self._session.execute(statement)

            if result.rowcount == 0:
                raise TaskNotFoundError("Task not found.")

            self._session.commit()
        except (SQLAlchemyError, TaskNotFoundError):
            self._session.rollback()
            raise

    def delete(self, *, task_id: int, user_id: int) -> None:
        """Delete a task only when it belongs to the given user."""
        statement = delete(TaskModel).where(
            TaskModel.id == task_id,
            TaskModel.user_id == user_id,
        )

        try:
            result = self._session.execute(statement)

            if result.rowcount == 0:
                raise TaskNotFoundError("Task not found.")

            self._session.commit()
        except (SQLAlchemyError, TaskNotFoundError):
            self._session.rollback()
            raise