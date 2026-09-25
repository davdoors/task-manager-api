"""Assemble the task manager API and initialize its database."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from api.db.models import Base
from api.db.session import engine
from api.exception_handlers import register_exception_handlers
from api.routers import auth, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create local database tables at startup and release connections on shutdown."""
    if engine.url.database and engine.url.database != ":memory:":
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Task Manager API", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
