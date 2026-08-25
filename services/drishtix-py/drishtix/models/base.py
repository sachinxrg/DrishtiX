"""
DrishtiX v4.0 — SQLAlchemy DeclarativeBase and engine factory.

Replaces the legacy Java DatabaseManager singleton. Creates the SQLite
engine with WAL mode for concurrent read access from multiple threads
(capture thread, recognition pool, UI thread).

The engine uses `check_same_thread=False` because SQLAlchemy manages its
own connection pool and thread safety; SQLite in WAL mode supports
concurrent readers with a single writer.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def create_db_engine(db_path: str = "data/drishtix.db") -> Engine:
    """
    Create and configure the SQLite engine with WAL mode and foreign keys.

    Args:
        db_path: Relative or absolute path to the SQLite database file.

    Returns:
        Configured SQLAlchemy Engine instance.
    """
    # Ensure the parent directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        pool_size=5,
        pool_pre_ping=True,
        echo=False,
    )

    # Enable WAL mode and foreign keys on every new connection
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    logger.info("SQLite engine created — path: %s, WAL mode enabled", db_file)
    return engine


def init_database(engine: Engine) -> None:
    """
    Create all tables defined by ORM models if they don't exist.

    This is the equivalent of the legacy DatabaseManager's implicit
    collection creation in MongoDB, but with explicit schema enforcement.

    Args:
        engine: The SQLAlchemy Engine instance.
    """
    Base.metadata.create_all(engine)
    logger.info("Database schema initialized — %d tables created/verified",
                len(Base.metadata.tables))


def create_session_factory(engine: Engine) -> sessionmaker:
    """
    Create a session factory bound to the given engine.

    Args:
        engine: The SQLAlchemy Engine instance.

    Returns:
        Configured sessionmaker instance.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)
