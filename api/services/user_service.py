"""Coordinate user registration independently of HTTP and database details."""

from api.core.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from api.core.security import PasswordHasher
from api.domain.user import User
from api.repositories.interfaces import UserRepository


class UserService:
    """Register users using an injected repository and password hasher."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def register_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Register validated, normalized input and return the persisted user."""

        if self._user_repository.get_by_username(username=username) is not None:
            raise UsernameAlreadyExistsError("Username is already registered.")

        if self._user_repository.get_by_email(email=email) is not None:
            raise EmailAlreadyExistsError("Email is already registered.")

        user = User(
            username=username,
            email=email,
            password_hash=self._password_hasher.hash(password),
        )
        return self._user_repository.add(user=user)
