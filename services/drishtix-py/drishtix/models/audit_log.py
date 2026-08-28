"""
DrishtiX v4.0 — AuditLog ORM model.

Migrated from: com.drishtix.model.AuditLogEntry (Java)
MongoDB collection: 'audit_log' → SQLite table: 'audit_log'
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from drishtix.models.base import Base


class AuditLog(Base):
    """
    System audit log entry.

    Records administrative actions (target added/deleted, config changed,
    gallery reloaded, data cleared) for accountability and debugging.
    """

    __tablename__ = "audit_log"

    audit_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"AuditLog(id={self.audit_id}, action='{self.action}', "
            f"entity={self.entity_type}#{self.entity_id}, time={self.timestamp})"
        )
