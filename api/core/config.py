"""Define application configuration."""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _mysql_url_from_env() -> str:
    """Build the MySQL connection URL from environment variables."""
    user = quote_plus(os.getenv("MYSQL_USER", "app"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", "app"))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "task_manager")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


DATABASE_URL = os.getenv("DATABASE_URL", _mysql_url_from_env())

# Define the encryption algorithm
ALGORITHM = "HS256"
# (days)
TOKEN_DURATION_DAYS = 7
# Define a secret to make the token even more secure, using a seed known only to the backend
# You can use OpenSSL in the terminal (openssl rand -hex 32)
# -> In a real project use an environment key
SECRET = "ac4e4397a4258350442050cb109872887bd72812b30d276cc1c1111e7a8253e2"