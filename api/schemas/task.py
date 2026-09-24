from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    AwareDatetime,
    field_validator
)
from datetime import datetime, timezone
from api.domain.enums import TaskStatus, TaskPriority

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=150)
    content: str = Field(default="", max_length=5000)
    deadline: AwareDatetime
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NOT_STARTED

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("deadline", mode="after")
    @classmethod
    def normalize_deadline(cls, value: datetime) -> datetime:
        """Convert the validated deadline to UTC."""
        return value.astimezone(timezone.utc)

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=150)
    content: str | None = Field(default=None, max_length=5000)
    deadline: AwareDatetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None

    @field_validator(
        "title", "content", "deadline", "priority", "status",
        mode="before",
    )
    @classmethod
    def reject_null_values(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field must not be null.")
        return value

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    deadline: AwareDatetime
    priority: TaskPriority
    status: TaskStatus
    user_id: int