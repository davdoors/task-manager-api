"""Configure the database engine and session factory."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from api.core.config import settings

# Setting check_same_thread=False allows a SQLite connection to be used from different threads when necessary.
# It does not make session objects safe to share concurrently between threads.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Enable foreign key enforcement for every SQLite connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)