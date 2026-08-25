"""
DrishtiX v4.0 — Audit DAO.

Repository for AuditLog entries.
Migrated from: com.drishtix.dao.AuditLogDAO (Java)
"""

import logging
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from drishtix.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditDAO:
    """Repository for system audit trail logs."""

    @staticmethod
    def log_action(
        session: Session,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist an audit log entry."""
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        session.add(entry)
        session.flush()
        logger.info("Audit: [%s] %s#%s - %s", action, entity_type, entity_id, details)
        return entry

    @staticmethod
    def get_recent(session: Session, limit: int = 100) -> list[AuditLog]:
        """Retrieve recent audit logs."""
        stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
        return list(session.execute(stmt).scalars().all())
