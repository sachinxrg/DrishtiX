"""
DrishtiX v4.0 — AppConfig ORM model.

Migrated from: com.drishtix.model.AlertConfig (Java)
MongoDB collection: 'alert_config' → SQLite table: 'app_config'

Expanded scope from alert-only config to application-wide key-value store.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from drishtix.models.base import Base


class AppConfig(Base):
    """
    Application configuration key-value store.

    Persists runtime-configurable parameters that can be modified through
    the Settings UI without editing config.yaml. Values stored as strings
    with type coercion methods for retrieval.
    """

    __tablename__ = "app_config"

    config_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def get_as_float(self) -> float:
        """Parse config_value as a float."""
        return float(self.config_value)

    def get_as_int(self) -> int:
        """Parse config_value as an integer."""
        return int(self.config_value)

    def get_as_bool(self) -> bool:
        """Parse config_value as a boolean (true/false, 1/0)."""
        return self.config_value.lower() in ("true", "1", "yes")

    def __repr__(self) -> str:
        return f"AppConfig({self.config_key}={self.config_value})"
