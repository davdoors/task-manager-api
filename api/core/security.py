"""Provide password hashing independently of HTTP and persistence.
"""

from typing import Any
from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from api.core.exceptions import AuthenticationError

class PasswordHasher:
    """Hash and verify passwords using Argon2id with random salts."""

    def __init__(self) -> None:
        self._hasher = Argon2PasswordHasher()

    def hash(self, password: str) -> str:
        """Hash the exact password without trimming or normalizing it."""
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Check a password against a stored hash, returning False on failure.

        The hash must come from trusted application storage, not user input.
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        if not isinstance(password_hash, str):
            raise TypeError("Password hash must be a string.")

        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False


class TokenManager:
    """Manage JWT tokens for authentication."""
    def __init__(self, *,secret: str, algorithm: str, duration_days: int) -> None:

        if not secret.strip():
            raise ValueError("Secret cannot be empty.")
        if not algorithm.strip():
            raise ValueError("Algorithm cannot be empty.")
        if isinstance(duration_days, bool) or not isinstance(duration_days, int):
            raise TypeError("Duration days must be an integer.")
        if duration_days <= 0:
            raise ValueError("Duration days must be positive.")

        self._secret = secret
        self._algorithm = algorithm
        self._duration_days = duration_days

    def create_access_token(self, user_id: int) -> str:
        """Create an access token for the user."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=self._duration_days)
        payload = {
            "sub": str(user_id),
            "exp": expires_at
        }
        return jwt.encode(payload, key=self._secret, algorithm=self._algorithm)


    def decode_access_token(self, token:str) -> dict[str, Any]:
        """Decode an access token."""
        try:
            return jwt.decode(
                token, 
                key=self._secret, 
                algorithms=[self._algorithm],
                options={"require_exp": True, "require_sub": True}
            )
        except JWTError as e:
            raise AuthenticationError("Invalid authentication credentials") from e