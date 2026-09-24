"""Define expected application errors independently of HTTP."""


class ApplicationError(Exception):
    """Base class for expected application errors."""


class TaskNotFoundError(ApplicationError):
    """Raised when a task is not found for the given user."""


class UsernameAlreadyExistsError(ApplicationError):
    """Raised when a username is already registered."""


class EmailAlreadyExistsError(ApplicationError):
    """Raised when an email is already registered."""


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""


class EmptyTaskUpdateError(ApplicationError):
    """Raised when a task update contains no fields."""
