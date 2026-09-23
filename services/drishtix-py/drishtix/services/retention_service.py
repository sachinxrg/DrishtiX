"""
DrishtiX v4.0 — Data Retention Enforcement Service.

Automatically purges expired detection logs and snapshot images based on
configurable retention periods (default: 30 days for both). Addresses
DPDP Act Section 8(7) requirement to erase personal data when purpose
is fulfilled.

Usage:
    Called periodically (e.g., daily) from a background timer or at startup.
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from drishtix.core.config import get_settings
from drishtix.core.constants import SNAPSHOTS_DIR
from drishtix.dao.session import get_session

logger = logging.getLogger(__name__)


class RetentionService:
    """
    Enforces data retention limits on snapshots and detection logs.
    """

    _instance: Optional["RetentionService"] = None

    @classmethod
    def get_instance(cls) -> "RetentionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def purge_expired_snapshots(self, retention_days: Optional[int] = None) -> int:
        """
        Delete snapshot image files older than the retention period.

        Args:
            retention_days: Override retention period. Uses config default if None.

        Returns:
            Number of snapshot files deleted.
        """
        settings = get_settings()
        days = retention_days or settings.alerts.snapshot_retention_days
        cutoff = time.time() - (days * 86400)
        deleted = 0

        if not SNAPSHOTS_DIR.exists():
            return 0

        for snapshot_file in SNAPSHOTS_DIR.iterdir():
            if not snapshot_file.is_file():
                continue
            try:
                if snapshot_file.stat().st_mtime < cutoff:
                    snapshot_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.debug("Failed to delete snapshot %s: %s", snapshot_file.name, e)

        if deleted > 0:
            logger.info("Retention purge: deleted %d expired snapshots (older than %d days)", deleted, days)
        return deleted

    def purge_expired_detection_logs(self, retention_days: Optional[int] = None) -> int:
        """
        Delete detection log records older than the retention period.

        Args:
            retention_days: Override retention period. Uses config default if None.

        Returns:
            Number of log records deleted.
        """
        settings = get_settings()
        days = retention_days or settings.database.log_retention_days
        cutoff_dt = datetime.now() - timedelta(days=days)

        try:
            from drishtix.models.detection_log import DetectionLog
            from sqlalchemy import delete as sql_delete

            with get_session() as session:
                stmt = (
                    sql_delete(DetectionLog)
                    .where(DetectionLog.detection_timestamp < cutoff_dt)
                )
                result = session.execute(stmt)
                count = result.rowcount

                if count > 0:
                    logger.info(
                        "Retention purge: deleted %d expired detection logs (older than %d days)",
                        count, days,
                    )
                return count
        except Exception as e:
            logger.error("Failed to purge expired detection logs: %s", e)
            return 0

    def run_full_purge(self) -> dict:
        """
        Run a complete retention enforcement cycle.

        Returns:
            Dict with counts of deleted snapshots and logs.
        """
        snapshots_deleted = self.purge_expired_snapshots()
        logs_deleted = self.purge_expired_detection_logs()

        # Audit trail for data purge operations
        if snapshots_deleted > 0 or logs_deleted > 0:
            try:
                from drishtix.dao.audit_dao import AuditDAO
                from drishtix.dao.session import get_session as _get_session

                with _get_session() as session:
                    AuditDAO.log_action(
                        session=session,
                        action="DATA_RETENTION_PURGE",
                        entity_type="System",
                        details=(
                            f"Purged {snapshots_deleted} expired snapshots, "
                            f"{logs_deleted} expired detection logs"
                        ),
                    )
            except Exception as e:
                logger.debug("Failed to write retention purge audit entry: %s", e)

        return {
            "snapshots_deleted": snapshots_deleted,
            "logs_deleted": logs_deleted,
        }
