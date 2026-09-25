"""Define application configuration."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "task_manager.db"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}", # use path in case env key doesn't exist
)

# Define the encryption algorithm
ALGORITHM = "HS256"
# (days)
TOKEN_DURATION_DAYS = 7
# Define a secret to make the token even more secure, using a seed known only to the backend
# You can use OpenSSL in the terminal (openssl rand -hex 32)
# -> In a real project use an environment key
SECRET = "ac4e4397a4258350442050cb109872887bd72812b30d276cc1c1111e7a8253e2"