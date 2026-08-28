"""
DrishtiX v4.0 — TargetRegistry ORM model.

Migrated from: com.drishtix.model.TargetRegistry (Java)
MongoDB collection: 'targets' → SQLite table: 'target_registry'

Key changes from legacy:
- BSON ObjectId → INTEGER AUTOINCREMENT primary key
- BSON category string → CHECK-constrained enum column
- Added SQLAlchemy relationships for images, embeddings, and detection logs
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drishtix.models.base import Base

if TYPE_CHECKING:
    from drishtix.models.detection_log import DetectionLog
    from drishtix.models.face_embedding import FaceEmbedding
    from drishtix.models.target_image import TargetImage


class TargetRegistry(Base):
    """
    Watchlist target entity.

    Represents a person of interest (criminal or missing person) in the
    surveillance system's watchlist. Each target can have multiple face
    images and pre-computed embedding vectors for gallery matching.
    """

    __tablename__ = "target_registry"

    target_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="CRIMINAL or MISSING_PERSON",
    )
    case_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    profile_image_path: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # ─── Relationships ──────────────────────────────────────────────
    images: Mapped[List["TargetImage"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
        order_by="TargetImage.image_order",
    )
    embeddings: Mapped[List["FaceEmbedding"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )
    detection_logs: Mapped[List["DetectionLog"]] = relationship(
        back_populates="target",
    )

    def __repr__(self) -> str:
        return (
            f"TargetRegistry(id={self.target_id}, name='{self.full_name}', "
            f"category={self.category}, active={self.is_active})"
        )
