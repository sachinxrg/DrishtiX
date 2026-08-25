"""
DrishtiX v4.0 — FaceEmbedding ORM model.

NEW table — does not exist in the legacy Java/MongoDB codebase.

The legacy system stored embedding vectors inline in MongoDB documents
within the 'targets' collection. This model externalizes embeddings into
a dedicated table with proper foreign key relationships, enabling:
- Multiple embeddings per target (one per uploaded face image)
- Efficient BLOB storage of 128-float vectors (512 bytes each)
- Gallery reconstruction via simple SELECT queries
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

import numpy as np
from sqlalchemy import DateTime, ForeignKey, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drishtix.models.base import Base

if TYPE_CHECKING:
    from drishtix.models.target_registry import TargetRegistry


class FaceEmbedding(Base):
    """
    SFace 128-dimensional face embedding vector.

    Stores pre-computed embedding vectors extracted from target face images
    using the SFace model. These vectors are loaded into the in-memory
    GalleryManager at startup for real-time cosine similarity matching.

    The embedding_vector is stored as a BLOB (raw bytes) using numpy's
    tobytes()/frombuffer() for zero-copy serialization of float32 arrays.
    """

    __tablename__ = "face_embedding"

    embedding_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("target_registry.target_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_image_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("target_image.image_id", ondelete="SET NULL"),
        nullable=True,
    )
    embedding_vector: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="128 float32 values as raw bytes (512 bytes)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # ─── Relationships ──────────────────────────────────────────────
    target: Mapped["TargetRegistry"] = relationship(back_populates="embeddings")

    # ─── Helper Methods ─────────────────────────────────────────────
    def get_vector(self) -> np.ndarray:
        """
        Deserialize the stored BLOB back into a numpy float32 array.

        Returns:
            128-dimensional numpy array of float32 values.
        """
        return np.frombuffer(self.embedding_vector, dtype=np.float32).copy()

    @staticmethod
    def from_vector(vector: np.ndarray) -> bytes:
        """
        Serialize a numpy float32 array into bytes for BLOB storage.

        Args:
            vector: 128-dimensional numpy array.

        Returns:
            Raw bytes representation (512 bytes for 128 float32s).
        """
        return vector.astype(np.float32).tobytes()

    def __repr__(self) -> str:
        return (
            f"FaceEmbedding(id={self.embedding_id}, target_id={self.target_id}, "
            f"dims={len(self.embedding_vector) // 4})"
        )
