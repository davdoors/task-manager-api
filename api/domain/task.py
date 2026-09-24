from datetime import datetime, timezone
from api.domain.enums import TaskStatus, TaskPriority
import api.domain.constants as constants

class Task:
    """Represent a user's task and its business behavior."""

    def __init__(
        self,
        *,
        title: str,
        content: str,
        deadline: datetime,
        user_id: int,
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.NOT_STARTED,
        task_id: int | None = None,
    ) -> None:
        self._validate_id(user_id, "user_id")

        if task_id is not None:
            self._validate_id(task_id, "task_id")

        self._id = task_id
        self._user_id = user_id
        self._title = self._validate_text(title, "title", constants.TASK_TITLE_MIN_LENGTH, constants.TASK_TITLE_MAX_LENGTH)
        self._content = self._validate_text(
            content, "content", constants.TASK_CONTENT_MIN_LENGTH, constants.TASK_CONTENT_MAX_LENGTH
        )
        self._deadline = self._normalize_datetime(deadline)

        self.change_priority(priority)
        self.change_status(status)

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def content(self) -> str:
        return self._content

    @property
    def deadline(self) -> datetime:
        return self._deadline

    @property
    def priority(self) -> TaskPriority:
        return self._priority

    @property
    def status(self) -> TaskStatus:
        return self._status

    @staticmethod
    def _validate_id(value: int, field_name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field_name} must be an integer.")

        if value <= 0:
            raise ValueError(f"{field_name} must be positive.")

    @staticmethod
    def _validate_text(
        value: str,
        field_name: str,
        min_length: int,
        max_length: int,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized_value = value.strip()

        if not min_length <= len(normalized_value) <= max_length:
            raise ValueError(
                f"{field_name} must contain between "
                f"{min_length} and {max_length} characters."
            )

        return normalized_value

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError("Date must be a datetime.")

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Date must include a timezone.")

        return value.astimezone(timezone.utc)

    def update_title(self, title: str) -> None:
        """Change the task title."""
        self._title = self._validate_text(title, "title", constants.TASK_TITLE_MIN_LENGTH, constants.TASK_TITLE_MAX_LENGTH)

    def update_content(self, content: str) -> None:
        """Replace the task description."""
        self._content = self._validate_text(
            content, "content", constants.TASK_CONTENT_MIN_LENGTH, constants.TASK_CONTENT_MAX_LENGTH
        )

    def reschedule(self, deadline: datetime) -> None:
        """Change the deadline, allowing past dates."""
        self._deadline = self._normalize_datetime(deadline)

    def change_status(self, status: TaskStatus) -> None:
        """Set any supported status, including reopening a task."""
        if not isinstance(status, TaskStatus):
            raise TypeError("Status must be a TaskStatus.")

        self._status = status

    def change_priority(self, priority: TaskPriority) -> None:
        """Set the task priority."""
        if not isinstance(priority, TaskPriority):
            raise TypeError("Priority must be a TaskPriority.")

        self._priority = priority

    def is_expired(self, now: datetime) -> bool:
        """Check whether the deadline has passed, regardless of status."""
        return self._deadline < self._normalize_datetime(now)