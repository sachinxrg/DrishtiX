"""
DrishtiX v4.0 — AppConfig DAO.

Repository for AppConfig key-value persistence.
Migrated from: com.drishtix.dao.AlertConfigDAO (Java)
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from drishtix.models.app_config import AppConfig

logger = logging.getLogger(__name__)


class ConfigDAO:
    """Repository for application runtime configuration settings."""

    @staticmethod
    def get_all(session: Session) -> list[AppConfig]:
        """Retrieve all configuration records."""
        stmt = select(AppConfig).order_by(AppConfig.config_key)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_value(session: Session, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a single config value by key, returning default if not found."""
        stmt = select(AppConfig).where(AppConfig.config_key == key)
        record = session.execute(stmt).scalar_one_or_none()
        return record.config_value if record else default

    @staticmethod
    def set_value(
        session: Session,
        key: str,
        value: str,
        description: Optional[str] = None,
    ) -> AppConfig:
        """Create or update a configuration key-value pair."""
        stmt = select(AppConfig).where(AppConfig.config_key == key)
        record = session.execute(stmt).scalar_one_or_none()

        if record:
            record.config_value = str(value)
            if description:
                record.description = description
        else:
            record = AppConfig(
                config_key=key,
                config_value=str(value),
                description=description,
            )
            session.add(record)

        session.flush()
        logger.info("Config set: %s = %s", key, value)
        return record

    @staticmethod
    def delete(session: Session, key: str) -> bool:
        """Delete a configuration key."""
        stmt = select(AppConfig).where(AppConfig.config_key == key)
        record = session.execute(stmt).scalar_one_or_none()
        if record:
            session.delete(record)
            return True
        return False
