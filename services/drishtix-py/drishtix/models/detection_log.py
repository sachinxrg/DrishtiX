"""
DrishtiX v4.0 — DetectionLog ORM model.

Migrated from: com.drishtix.model.DetectionLog (Java)
MongoDB collection: 'detection_logs' → SQLite table: 'detection_log'

Key changes from legacy:
- matchConfidenceScore (LBPH distance) → match_confidence (cosine similarity 0.0–1.0)
- Removed getConfidenceDisplay() inversion logic (cosine similarity is already intuitive)
- Added proper FK constraints to target_registry and camera_source
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drishtix.models.base import Base

if TYPE_CHECKING:
    from drishtix.models.camera_source import CameraSource
    from drishtix.models.target_registry import TargetRegistry


class DetectionLog(Base):
    """
    Detection event log entry.

    Created each time a recognized target is spotted on a live camera feed
    or in a scanned image. Stores the match confidence, a snapshot path,
    and references to the matched target and source camera.
    """

    __tablename__ = "detection_log"

    log_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("target_registry.target_id"),
        nullable=False,
        index=True,
    )
    camera_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("camera_source.camera_id"),
        nullable=True,
    )
    match_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Cosine similarity score (0.0 to 1.0)",
    )
    snapshot_path: Mapped[Optional[str]] = mapped_column(String(500))
    location_tag: Mapped[Optional[str]] = mapped_column(String(255))
    detection_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # ─── Relationships ──────────────────────────────────────────────
    target: Mapped["TargetRegistry"] = relationship(back_populates="detection_logs")
    camera: Mapped[Optional["CameraSource"]] = relationship()

    @property
    def confidence_display(self) -> str:
        """Format confidence as a percentage string (e.g., '92.4%')."""
        return f"{self.match_confidence * 100:.1f}%"

    def __repr__(self) -> str:
        return (
            f"DetectionLog(id={self.log_id}, target_id={self.target_id}, "
            f"confidence={self.match_confidence:.3f}, time={self.detection_timestamp})"
        )
