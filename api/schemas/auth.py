from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1, repr=False)
    token_type: Literal["Bearer"] = "Bearer"

    @field_validator("access_token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        """Reject whitespace without modifying the token."""
        if any(character.isspace() for character in value):
            raise ValueError("Token must not contain whitespace.")
        return value
