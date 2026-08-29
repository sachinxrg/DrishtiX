"""
DrishtiX v4.0 — Database session management.

Provides a thread-safe session factory and context manager for database
operations. Replaces the legacy DatabaseManager.getInstance() pattern
with Python's context manager protocol.

Usage:
    from drishtix.dao.session import get_session

    with get_session() as session:
        targets = session.query(TargetRegistry).all()
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from drishtix.models.base import create_db_engine, create_session_factory, init_database

logger = logging.getLogger(__name__)

# Module-level singletons — initialized once at startup
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def initialize(db_path: str = "data/drishtix.db", encryption_key: str = "") -> None:
    """
    Initialize the database engine, create tables, and configure the session factory.

    Must be called once at application startup before any DAO operations.

    Args:
        db_path: Path to the SQLite database file.
        encryption_key: Optional SQLCipher encryption passphrase.
    """
    global _engine, _session_factory

    _engine = create_db_engine(db_path, encryption_key=encryption_key)
    init_database(_engine)
    _session_factory = create_session_factory(_engine)

    logger.info("Database session factory initialized — path: %s", db_path)


def get_engine() -> Engine:
    """Return the global SQLAlchemy engine. Raises if not initialized."""
    if _engine is None:
        raise RuntimeError(
            "Database not initialized. Call drishtix.dao.session.initialize() first."
        )
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional session scope via context manager.

    Commits on success, rolls back on exception, and always closes the session.

    Yields:
        SQLAlchemy Session instance.
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call drishtix.dao.session.initialize() first."
        )

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """
    Test the database connection by executing a simple query.

    Returns:
        True if the connection is healthy, False otherwise.
    """
    try:
        if _engine is None:
            return False
        with _engine.connect() as conn:
            conn.execute(conn.engine.dialect.do_ping(conn))
        return True
    except Exception as e:
        logger.error("Database connection test failed: %s", e)
        return False


def shutdown() -> None:
    """Dispose of the engine and close all connections."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        logger.info("Database engine disposed")
    _engine = None
    _session_factory = None
