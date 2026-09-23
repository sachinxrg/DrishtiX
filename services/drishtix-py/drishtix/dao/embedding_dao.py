"""
DrishtiX v4.0 — Embedding DAO.

New DAO for the face_embedding table. Handles CRUD operations for
SFace embedding vectors used in gallery matching.
"""

import logging
from typing import Optional

import numpy as np
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.orm import Session

from drishtix.models.face_embedding import FaceEmbedding

logger = logging.getLogger(__name__)


class EmbeddingDAO:
    """Repository for FaceEmbedding CRUD and gallery loading operations."""

    @staticmethod
    def get_all_for_target(session: Session, target_id: int) -> list[FaceEmbedding]:
        """Retrieve all embeddings for a specific target."""
        stmt = (
            select(FaceEmbedding)
            .where(FaceEmbedding.target_id == target_id)
            .order_by(FaceEmbedding.created_at)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_active_embeddings(session: Session) -> list[FaceEmbedding]:
        """
        Retrieve all embeddings for active targets.

        Used at startup to populate the in-memory GalleryManager.
        Joins with target_registry to filter by is_active=True.
        """
        from drishtix.models.target_registry import TargetRegistry

        stmt = (
            select(FaceEmbedding)
            .join(TargetRegistry)
            .where(TargetRegistry.is_active.is_(True))
            .order_by(FaceEmbedding.target_id, FaceEmbedding.created_at)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def create(
        session: Session,
        target_id: int,
        vector: np.ndarray,
        source_image_id: Optional[int] = None,
        model_version: Optional[str] = None,
    ) -> FaceEmbedding:
        """
        Store a new embedding vector for a target.

        Args:
            session: SQLAlchemy session.
            target_id: ID of the target this embedding belongs to.
            vector: 128 or 512-dimensional numpy float32 array.
            source_image_id: Optional ID of the source TargetImage.
            model_version: Model identifier (e.g. 'sface_128', 'arcface_512').

        Returns:
            The created FaceEmbedding entity.
        """
        # Auto-detect model version from vector dimensionality if not specified
        if model_version is None:
            dim = vector.shape[0] if vector.ndim == 1 else 0
            model_version = f"auto_{dim}d"

        embedding = FaceEmbedding(
            target_id=target_id,
            source_image_id=source_image_id,
            embedding_vector=FaceEmbedding.from_vector(vector),
            model_version=model_version,
        )
        session.add(embedding)
        session.flush()
        logger.info(
            "Embedding created: id=%d, target_id=%d, dims=%d, model=%s",
            embedding.embedding_id, target_id, len(vector), model_version,
        )
        return embedding

    @staticmethod
    def delete_for_target(session: Session, target_id: int) -> int:
        """
        Delete all embeddings for a target.

        Returns:
            Number of deleted embeddings.
        """
        stmt = (
            sql_delete(FaceEmbedding)
            .where(FaceEmbedding.target_id == target_id)
        )
        result = session.execute(stmt)
        count = result.rowcount
        logger.info("Deleted %d embeddings for target_id=%d", count, target_id)
        return count

    @staticmethod
    def delete_for_image(session: Session, source_image_id: int) -> int:
        """Delete all embeddings associated with a specific source image."""
        stmt = (
            sql_delete(FaceEmbedding)
            .where(FaceEmbedding.source_image_id == source_image_id)
        )
        result = session.execute(stmt)
        return result.rowcount

    @staticmethod
    def count_for_target(session: Session, target_id: int) -> int:
        """Return the number of embeddings for a target."""
        from sqlalchemy import func
        stmt = (
            select(func.count())
            .select_from(FaceEmbedding)
            .where(FaceEmbedding.target_id == target_id)
        )
        return session.execute(stmt).scalar_one()
