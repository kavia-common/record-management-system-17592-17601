"""
Database setup and session management for the application.
Uses SQLite via SQLAlchemy for persistence.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Note on configuration:
# In a production setup, read the DB URL from an environment variable.
# For this exercise, we default to a local SQLite file.
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# For SQLite, check_same_thread must be False when using threads (e.g., FastAPI)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a SQLAlchemy session.
    Ensures the session is closed after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager for non-request scoped scripts (e.g., migrations, scripts).
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
