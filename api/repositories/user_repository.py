"""Persist domain users using SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from api.core.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from api.db.models import UserModel
from api.domain.user import User
from api.repositories.interfaces import UserRepository


class SQLiteUserRepository(UserRepository):
    """Persist users through an injected session.

    Each write commits its transaction. The caller owns the session lifetime
    and must not mix unrelated pending writes into the same transaction.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, *, user: User) -> User:
        """Insert a new user and return it with its generated ID."""
        if user.id is not None:
            raise ValueError("A new user must not already have an ID.")

        model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
        )
        try:
            self._session.add(model)
            self._session.flush()
            persisted_user = self._to_domain(model)
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if self.get_by_username(username=user.username) is not None:
                raise UsernameAlreadyExistsError(
                    "Username is already registered."
                ) from error
            if self.get_by_email(email=user.email) is not None:
                raise EmailAlreadyExistsError(
                    "Email is already registered."
                ) from error
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise

        return persisted_user

    def get_by_id(self, *, user_id: int) -> User | None:
        """Return a user by primary key, or None if not found."""
        model = self._session.get(UserModel, user_id)
        return self._to_domain(model) if model is not None else None

    def get_by_username(self, *, username: str) -> User | None:
        """Return a user by normalized username, or None."""
        statement = select(UserModel).where(UserModel.username == username)
        model = self._session.scalar(statement)
        return self._to_domain(model) if model is not None else None

    def get_by_email(self, *, email: str) -> User | None:
        """Return a user by email, or None."""
        statement = select(UserModel).where(UserModel.email == email)
        model = self._session.scalar(statement)
        return self._to_domain(model) if model is not None else None

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convert a database model into an immutable domain entity."""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
        )
