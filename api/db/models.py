"""Define SQLAlchemy tables without opening database connections.

SQLite connections must enable PRAGMA foreign_keys = ON in the session layer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, Column, Integer
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import TypeDecorator

from api.domain import constants
from api.domain.enums import TaskPriority, TaskStatus


class UTCDateTime(TypeDecorator[datetime]):
    """Store naive UTC timestamps and restore timezone-aware UTC values.

    SQLite does not preserve timezone information. Reject naive input so that
    conversion never depends on the machine's local timezone.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, datetime):
            raise TypeError("Date must be a datetime.")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Date must include a timezone.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    """Collect table metadata for explicit initialization by the application."""


class UserModel(Base):
    """Persist registered users and their password hashes."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"length(username) BETWEEN {constants.USER_USERNAME_MIN_LENGTH} "
            f"AND {constants.USER_USERNAME_MAX_LENGTH}",
            name="ck_users_username_length",
        ),
        CheckConstraint(
            f"length(email) BETWEEN {constants.USER_EMAIL_MIN_LENGTH} "
            f"AND {constants.USER_EMAIL_MAX_LENGTH}",
            name="ck_users_email_length",
        ),
        CheckConstraint(
            "length(password_hash) > 0",
            name="ck_users_password_hash_not_empty",
        ),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(constants.USER_USERNAME_MAX_LENGTH), unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)

    # Let the foreign key reject deletion instead of deleting or detaching tasks.
    tasks = relationship(
        "TaskModel", back_populates="user", passive_deletes="all"
    )


class TaskModel(Base):
    """Persist tasks owned by a single registered user."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            f"length(trim(title)) BETWEEN {constants.TASK_TITLE_MIN_LENGTH} "
            f"AND {constants.TASK_TITLE_MAX_LENGTH}",
            name="ck_tasks_title_length",
        ),
        CheckConstraint(
            f"length(content) BETWEEN {constants.TASK_CONTENT_MIN_LENGTH} "
            f"AND {constants.TASK_CONTENT_MAX_LENGTH}",
            name="ck_tasks_content_length",
        ),
        Index("ix_tasks_user_id_deadline", "user_id", "deadline"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(
        String(constants.TASK_TITLE_MAX_LENGTH), nullable=False
    )
    content = Column(Text, nullable=False, default="", server_default="")
    deadline = Column(UTCDateTime(), nullable=False)
    status = Column(
        Enum(
            TaskStatus,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="ck_tasks_status",
        ),
        nullable=False,
        default=TaskStatus.NOT_STARTED,
        server_default=TaskStatus.NOT_STARTED.value,
    )
    priority = Column(
        Enum(
            TaskPriority,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="ck_tasks_priority",
        ),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    user = relationship("UserModel", back_populates="tasks")
