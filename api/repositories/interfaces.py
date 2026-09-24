from abc import ABC, abstractmethod
from datetime import datetime

from api.domain.task import Task
from api.domain.user import User

class TaskRepository(ABC):
    @abstractmethod
    def add(self, *, task: Task) -> Task:
        """ Add new task to the repository, and return it with its ID. """
        pass

    @abstractmethod
    def get_by_id_for_user(self, *, task_id: int, user_id: int) -> Task | None:
        """ Return the user's task, or None if not found. """
        pass

    @abstractmethod
    def list_by_user(self, *, user_id: int) -> list[Task]:
        """ Return all tasks for a specific user. """
        pass

    @abstractmethod
    def list_expired(self, *, user_id: int, now: datetime) -> list[Task]:
        """ Return all expired tasks for a specific user. """
        pass

    @abstractmethod
    def update(self, *, task: Task) -> None:
        """Update an existing task matching its ID and owner.

        Raise TaskNotFoundError if no matching task exists.
        """
        pass

    @abstractmethod
    def delete(self, *, task_id: int, user_id: int) -> None:
        """Delete a task matching its ID and owner.

        Raise TaskNotFoundError if no matching task exists.
        """
        pass

class UserRepository(ABC):
    @abstractmethod
    def add(self, *, user: User) -> User:
        """ Add new user to the repository, and return it with its ID. """
        pass

    @abstractmethod
    def get_by_id(self, *, user_id: int) -> User | None:
        """ Retrieve a user by its ID. """
        pass

    @abstractmethod
    def get_by_username(self, *, username: str) -> User | None:
        """ Retrieve a user by its username. """
        pass

    @abstractmethod
    def get_by_email(self, *, email: str) -> User | None:
        """ Retrieve a user by its email. """
        pass


