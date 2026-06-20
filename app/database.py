"""
Database session = your Drizzle `db` client, but accessed via FastAPI's
dependency-injection system instead of importing a global.

In Express you imported `db` and used it directly. FastAPI's idiom is a
`get_db()` dependency that opens a session per-request and closes it after —
this guarantees connections are always released, even on errors. Routes receive
the session as an argument (see routes/invoices.py).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import settings
from .models import Base

# For SQLite (the default learning DB) we need this connect arg; Postgres ignores it.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create tables if they don't exist — the dev-time equivalent of
    `drizzle-kit push`. (For real Postgres you'd use Alembic migrations.)"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yields a session per request, then closes it. Used as a FastAPI Depends()."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
