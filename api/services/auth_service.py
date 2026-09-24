"""Check user credentials independently of HTTP."""

from api.core.exceptions import AuthenticationError
from api.core.security import PasswordHasher
from api.domain.user import User
from api.repositories.interfaces import UserRepository


class AuthService:
    """Authenticate users with a repository and a password hasher."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def authenticate_user(self, *, username: str, password: str) -> User:
        """Return the user when the credentials are valid."""
        user = self._user_repository.get_by_username(
            username=username.strip().lower(),
        )

        if user is None:
            raise AuthenticationError("Invalid username or password.")

        if not self._password_hasher.verify(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")

        return user
