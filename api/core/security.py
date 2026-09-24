"""Provide password hashing independently of HTTP and persistence.
"""

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


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
