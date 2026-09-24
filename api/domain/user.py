from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    """Represent a registered user in the domain."""

    username: str
    email: str
    password_hash: str = field(repr=False)
    id: int | None = None