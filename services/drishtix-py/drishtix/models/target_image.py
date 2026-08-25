"""
DrishtiX v4.0 — TargetImage ORM model.

Migrated from: com.drishtix.model.TargetImage (Java)
MongoDB collection: 'target_images' → SQLite table: 'target_image'

Key changes from legacy:
- Dropped 'templatePath' column (SFace doesn't use LBPH templates)
- Added foreign key constraint to target_registry
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drishtix.models.base import Base

if TYPE_CHECKING:
    from drishtix.models.target_registry import TargetRegistry


class TargetImage(Base):
    """
    Face image associated with a watchlist target.

    Each target can have up to 5 images for improved recognition accuracy.
    When an image is uploaded, SFace automatically extracts and stores
    the 128-dim embedding vector in the face_embedding table.
    """

    __tablename__ = "target_image"

    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("target_registry.target_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    image_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # ─── Relationships ──────────────────────────────────────────────
    target: Mapped["TargetRegistry"] = relationship(back_populates="images")

    def __repr__(self) -> str:
        return (
            f"TargetImage(id={self.image_id}, target_id={self.target_id}, "
            f"order={self.image_order})"
        )
