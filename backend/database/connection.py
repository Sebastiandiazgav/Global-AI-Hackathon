"""
MyAgent - Database Connection
Manages PostgreSQL connection pool using SQLAlchemy.
Falls back to in-memory store if database is unavailable.
"""

import os
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import OperationalError

from config import get_settings


_engine = None
_SessionLocal = None
_db_available = None


def _get_engine():
    """Create or return the database engine singleton."""
    global _engine
    if _engine is not None:
        return _engine

    settings = get_settings()
    database_url = settings.database_url

    if not database_url or database_url.startswith("sqlite"):
        # Use SQLite for local dev if no PostgreSQL URL
        _engine = create_engine(
            "sqlite:///myagent_local.db",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False,
        )

    return _engine


def _get_session_factory():
    """Create or return the session factory."""
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal

    engine = _get_engine()
    _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal


def is_database_available() -> bool:
    """Check if the database is reachable."""
    global _db_available
    if _db_available is not None:
        return _db_available

    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_available = True
    except (OperationalError, Exception):
        _db_available = False

    return _db_available


@contextmanager
def get_db_session():
    """Get a database session context manager."""
    SessionLocal = _get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """Initialize the database schema (create tables if not exist)."""
    from pathlib import Path

    if not is_database_available():
        print("⚠️  Database not available. Using in-memory fallback.")
        return False

    engine = _get_engine()
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        print("⚠️  schema.sql not found. Skipping DB init.")
        return False

    try:
        schema_sql = schema_file.read_text(encoding="utf-8")
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
        with engine.connect() as conn:
            for statement in statements:
                if statement and not statement.startswith("--"):
                    try:
                        conn.execute(text(statement))
                    except Exception:
                        # Skip statements that fail (e.g., IF NOT EXISTS already created)
                        pass
            conn.commit()
        print("✅ Database schema initialized")
        return True
    except Exception as e:
        print(f"⚠️  Database init failed: {e}. Using in-memory fallback.")
        return False


def reset_availability_cache():
    """Reset the availability cache (useful for testing)."""
    global _db_available
    _db_available = None
