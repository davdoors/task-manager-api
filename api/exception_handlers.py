"""Translate expected application errors into HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.core.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    EmptyTaskUpdateError,
    TaskNotFoundError,
    UsernameAlreadyExistsError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register only expected errors; leave unexpected failures as server errors."""
    status_codes = {
        TaskNotFoundError: 404,
        UsernameAlreadyExistsError: 409,
        EmailAlreadyExistsError: 409,
        EmptyTaskUpdateError: 400,
        AuthenticationError: 401,
    }

    for error_type, status_code in status_codes.items():
        app.add_exception_handler(error_type, _make_handler(status_code))


def _make_handler(status_code: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
            headers=headers,
        )

    return handler
