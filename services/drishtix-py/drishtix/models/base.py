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

from drishtix.core.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def create_db_engine(db_path: str = "data/drishtix.db", encryption_key: str = "") -> Engine:
    """
    Create and configure the SQLite engine with WAL mode and foreign keys.

    When encryption_key is non-empty, applies PRAGMA key for SQLCipher
    at-rest encryption (requires pysqlcipher3 or equivalent driver).

    Args:
        db_path: Relative or absolute path to the SQLite database file.
        encryption_key: Optional SQLCipher encryption passphrase.

    Returns:
        Configured SQLAlchemy Engine instance.
    """
    # Ensure the parent directory exists.
    # A relative db_path is anchored to the project root, not the current
    # working directory: the default "data/drishtix.db" otherwise resolved
    # against wherever the process was launched from, so starting the app
    # from another directory created a brand-new empty database there and
    # the operator's entire watchlist appeared to have vanished.
    # Absolute paths are honoured as given (the tests pass tmp_path).
    db_file = Path(db_path)
    if not db_file.is_absolute():
        db_file = PROJECT_ROOT / db_file
    db_file.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        pool_size=5,
        pool_pre_ping=True,
        echo=False,
    )

    # Capture encryption_key in closure for the event listener
    _enc_key = encryption_key

    # Enable WAL mode and foreign keys on every new connection
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        # SQLCipher encryption: must be first PRAGMA after connection
        if _enc_key:
            cursor.execute(f"PRAGMA key='{_enc_key}'")
            logger.info("SQLCipher encryption enabled for database.")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    logger.info("SQLite engine created — path: %s, WAL mode enabled", db_file)
    return engine


def init_database(engine: Engine) -> None:
    """
    Create all tables defined by ORM models and perform schema synchronization.

    1. Creates any missing tables defined in Base.metadata.
    2. Auto-migrates missing columns in existing SQLite tables (e.g. model_version).

    Args:
        engine: The SQLAlchemy Engine instance.
    """
    # Ensure all ORM models are imported so Base.metadata is populated
    import drishtix.models.app_config  # noqa: F401
    import drishtix.models.audit_log  # noqa: F401
    import drishtix.models.camera_source  # noqa: F401
    import drishtix.models.consent_record  # noqa: F401
    import drishtix.models.detection_log  # noqa: F401
    import drishtix.models.face_embedding  # noqa: F401
    import drishtix.models.target_image  # noqa: F401
    import drishtix.models.target_registry  # noqa: F401

    Base.metadata.create_all(engine)

    # Lightweight schema migration for SQLite: add any missing columns
    with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            result = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
            existing_cols = {row[1] for row in result.fetchall()}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(engine.dialect)
                    default_clause = ""
                    if col.server_default is not None:
                        default_clause = f" DEFAULT {col.server_default.arg}"
                    elif col.default is not None and col.default.is_scalar:
                        default_clause = f" DEFAULT '{col.default.arg}'"
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                    logger.info("Migrating schema: adding missing column via '%s'", alter_sql)
                    conn.execute(text(alter_sql))
        conn.commit()

    logger.info(
        "Database schema initialized — %d tables created/verified",
        len(Base.metadata.tables),
    )


def create_session_factory(engine: Engine) -> sessionmaker:
    """
    Create a session factory bound to the given engine.

    Args:
        engine: The SQLAlchemy Engine instance.

    Returns:
        Configured sessionmaker instance.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)
