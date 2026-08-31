"""SQLAlchemy engine/session setup.

Using SQLAlchemy (rather than a specific driver) lets the database backend
be swapped between SQLite (local dev default) and MySQL (production) purely
through the DATABASE_URL environment variable.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLite needs this connect arg when used across threads (FastAPI's
# threadpool for sync request handlers). Other databases (e.g. MySQL)
# ignore it.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db():
    """FastAPI dependency that yields a database session per-request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import models so they are registered on Base.metadata before creating.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
