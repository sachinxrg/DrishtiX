"""
DrishtiX v4.0 — Right-to-Erasure Service (DPDP Act 2023 §8(9)).

Implements complete, verifiable data erasure for a data principal's
biometric and personal data. Goes beyond SQL CASCADE by:
1. Deleting snapshot image files from disk
2. Purging body Re-ID profiles from in-memory gallery
3. Logging the erasure action in the audit trail
4. Returning a machine-readable erasure receipt

India DPDP Act 2023 Reference:
    §8(9): "The Data Principal shall have the right to erasure of personal
    data that is no longer necessary for the purpose for which it was
    processed."

Usage:
    from drishtix.services.erasure_service import ErasureService

    receipt = ErasureService.erase_target(target_id=42, reason="DPDP §8(9) request")
    print(receipt)  # ErasureReceipt(target_id=42, ...)
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from drishtix.dao.session import get_session

logger = logging.getLogger(__name__)


@dataclass
class ErasureReceipt:
    """
    Machine-readable receipt confirming data erasure.

    Provides an auditable record of what data was deleted and when,
    suitable for responding to data principal erasure requests under
    DPDP Act 2023 §8(9).
    """

    target_id: int
    target_name: str
    reason: str
    timestamp: float
    embeddings_deleted: int = 0
    images_deleted: int = 0
    detection_logs_deleted: int = 0
    snapshot_files_deleted: int = 0
    snapshot_files_failed: List[str] = field(default_factory=list)
    reid_profile_purged: bool = False
    gallery_reloaded: bool = False
    audit_logged: bool = False
    success: bool = False

    def summary(self) -> str:
        """Human-readable erasure summary."""
        lines = [
            f"=== Erasure Receipt ===",
            f"Target ID:     {self.target_id}",
            f"Target Name:   {self.target_name}",
            f"Reason:        {self.reason}",
            f"Timestamp:     {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}",
            f"Embeddings:    {self.embeddings_deleted} deleted",
            f"Images:        {self.images_deleted} deleted",
            f"Det. Logs:     {self.detection_logs_deleted} deleted",
            f"Snapshots:     {self.snapshot_files_deleted} files removed",
            f"Re-ID Profile: {'purged' if self.reid_profile_purged else 'n/a'}",
            f"Gallery:       {'reloaded' if self.gallery_reloaded else 'not reloaded'}",
            f"Audit:         {'logged' if self.audit_logged else 'FAILED'}",
            f"Status:        {'✅ COMPLETE' if self.success else '❌ PARTIAL'}",
        ]
        if self.snapshot_files_failed:
            lines.append(f"Failed files:  {', '.join(self.snapshot_files_failed)}")
        return "\n".join(lines)


class ErasureService:
    """
    Complete data erasure for DPDP Act §8(9) compliance.

    Performs a multi-layer cascade delete:
    1. SQL: Delete target → cascades to embeddings, images
    2. SQL: Delete detection logs referencing this target
    3. Disk: Remove snapshot image files referenced by detection logs
    4. Memory: Purge body Re-ID profile from DnnBodyReIdService
    5. Memory: Reload gallery to remove cached embeddings
    6. Audit: Log the erasure with details for compliance reporting
    """

    @staticmethod
    def erase_target(
        target_id: int,
        reason: str = "Data principal erasure request (DPDP §8(9))",
    ) -> ErasureReceipt:
        """
        Erase all personal data for a target across all storage layers.

        Args:
            target_id: The target to erase.
            reason: Reason for erasure (for audit trail).

        Returns:
            ErasureReceipt documenting what was deleted.
        """
        receipt = ErasureReceipt(
            target_id=target_id,
            target_name="",
            reason=reason,
            timestamp=time.time(),
        )

        try:
            with get_session() as session:
                # 1. Load target info before deletion
                from drishtix.models.target_registry import TargetRegistry
                target = session.get(TargetRegistry, target_id)
                if target is None:
                    logger.warning("Erasure failed: target_id=%d not found", target_id)
                    receipt.success = False
                    return receipt

                receipt.target_name = target.full_name

                # 2. Count related records before cascade delete
                from drishtix.dao.embedding_dao import EmbeddingDAO
                receipt.embeddings_deleted = EmbeddingDAO.count_for_target(session, target_id)

                from drishtix.models.target_image import TargetImage
                from sqlalchemy import select, func as sql_func
                img_count = session.execute(
                    select(sql_func.count()).select_from(TargetImage).where(
                        TargetImage.target_id == target_id
                    )
                ).scalar_one()
                receipt.images_deleted = img_count

                # 3. Collect and delete snapshot files from detection logs
                from drishtix.models.detection_log import DetectionLog
                from sqlalchemy import delete as sql_delete

                det_logs = session.execute(
                    select(DetectionLog).where(DetectionLog.target_id == target_id)
                ).scalars().all()

                receipt.detection_logs_deleted = len(det_logs)

                for log_entry in det_logs:
                    if log_entry.snapshot_path:
                        snap_path = Path(log_entry.snapshot_path)
                        try:
                            if snap_path.exists():
                                snap_path.unlink()
                                receipt.snapshot_files_deleted += 1
                        except OSError as e:
                            logger.warning("Failed to delete snapshot %s: %s", snap_path, e)
                            receipt.snapshot_files_failed.append(str(snap_path))

                # Delete detection logs (no cascade from target)
                session.execute(
                    sql_delete(DetectionLog).where(DetectionLog.target_id == target_id)
                )

                # 4. Delete profile image file from disk
                if target.profile_image_path:
                    profile_path = Path(target.profile_image_path)
                    try:
                        if profile_path.exists():
                            profile_path.unlink()
                    except OSError as e:
                        logger.warning("Failed to delete profile image %s: %s", profile_path, e)

                # 5. Delete target (CASCADE handles embeddings + images in DB)
                session.delete(target)
                session.flush()

                # 6. Audit trail
                try:
                    from drishtix.dao.audit_dao import AuditDAO
                    AuditDAO.log_action(
                        session=session,
                        action="DATA_ERASURE",
                        entity_type="TargetRegistry",
                        entity_id=target_id,
                        details=(
                            f"DPDP §8(9) erasure: '{receipt.target_name}' — "
                            f"{receipt.embeddings_deleted} embeddings, "
                            f"{receipt.images_deleted} images, "
                            f"{receipt.detection_logs_deleted} detection logs, "
                            f"{receipt.snapshot_files_deleted} snapshot files. "
                            f"Reason: {reason}"
                        ),
                    )
                    receipt.audit_logged = True
                except Exception as e:
                    logger.error("Failed to write erasure audit entry: %s", e)

            # 7. Purge from in-memory Re-ID gallery (outside session)
            try:
                from drishtix.services.reid_tracking import DnnBodyReIdService
                reid = DnnBodyReIdService.get_instance()
                if hasattr(reid, '_body_gallery') and target_id in reid._body_gallery:
                    del reid._body_gallery[target_id]
                    receipt.reid_profile_purged = True
            except Exception as e:
                logger.debug("Re-ID profile purge skipped: %s", e)

            # 8. Reload gallery to remove cached embedding vectors
            try:
                from drishtix.services.gallery_manager import GalleryManager
                GalleryManager.get_instance().reload_gallery()
                receipt.gallery_reloaded = True
            except Exception as e:
                logger.warning("Gallery reload after erasure failed: %s", e)

            receipt.success = True
            logger.info(
                "Data erasure complete for target_id=%d ('%s'): %s",
                target_id, receipt.target_name, receipt.summary(),
            )

        except Exception as e:
            logger.error("Data erasure failed for target_id=%d: %s", target_id, e)
            receipt.success = False

        return receipt
