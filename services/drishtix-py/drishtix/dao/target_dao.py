"""
DrishtiX v4.0 — Target DAO.

Migrated from: com.drishtix.dao.TargetDAO + TargetImageDAO (Java)
Handles CRUD operations for TargetRegistry and TargetImage entities.
"""

import logging
from typing import Optional

from sqlalchemy import select, func as sql_func
from sqlalchemy.orm import Session, joinedload

from drishtix.models.target_registry import TargetRegistry
from drishtix.models.target_image import TargetImage

logger = logging.getLogger(__name__)


class TargetDAO:
    """Repository for TargetRegistry and TargetImage CRUD operations."""

    @staticmethod
    def get_all(session: Session, active_only: bool = False) -> list[TargetRegistry]:
        """
        Retrieve all targets, optionally filtered by active status.

        Args:
            session: SQLAlchemy session.
            active_only: If True, return only active targets.

        Returns:
            List of TargetRegistry entities with eagerly loaded images.
        """
        stmt = (
            select(TargetRegistry)
            .options(joinedload(TargetRegistry.images))
            .order_by(TargetRegistry.full_name)
        )
        if active_only:
            stmt = stmt.where(TargetRegistry.is_active.is_(True))
        return list(session.execute(stmt).unique().scalars().all())

    @staticmethod
    def get_by_id(session: Session, target_id: int) -> Optional[TargetRegistry]:
        """Retrieve a single target by ID with eagerly loaded relationships."""
        stmt = (
            select(TargetRegistry)
            .options(
                joinedload(TargetRegistry.images),
                joinedload(TargetRegistry.embeddings),
            )
            .where(TargetRegistry.target_id == target_id)
        )
        return session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_by_category(session: Session, category: str) -> list[TargetRegistry]:
        """Retrieve all active targets of a specific category."""
        stmt = (
            select(TargetRegistry)
            .where(
                TargetRegistry.category == category,
                TargetRegistry.is_active.is_(True),
            )
            .order_by(TargetRegistry.full_name)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def search(session: Session, query: str) -> list[TargetRegistry]:
        """Search targets by name or case number (case-insensitive partial match)."""
        pattern = f"%{query}%"
        stmt = (
            select(TargetRegistry)
            .where(
                (TargetRegistry.full_name.ilike(pattern))
                | (TargetRegistry.case_number.ilike(pattern))
            )
            .order_by(TargetRegistry.full_name)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def create(session: Session, target: TargetRegistry) -> TargetRegistry:
        """Insert a new target into the database."""
        session.add(target)
        session.flush()  # Assign the auto-generated target_id
        logger.info("Target created: id=%d, name='%s'", target.target_id, target.full_name)
        return target

    @staticmethod
    def update(session: Session, target: TargetRegistry) -> TargetRegistry:
        """Update an existing target (merge into session)."""
        merged = session.merge(target)
        session.flush()
        logger.info("Target updated: id=%d, name='%s'", merged.target_id, merged.full_name)
        return merged

    @staticmethod
    def delete(session: Session, target_id: int) -> bool:
        """
        Delete a target and all associated images/embeddings (cascade).

        Returns:
            True if the target was found and deleted, False otherwise.
        """
        target = session.get(TargetRegistry, target_id)
        if target is None:
            logger.warning("Delete failed — target_id=%d not found", target_id)
            return False
        session.delete(target)
        logger.info("Target deleted: id=%d, name='%s'", target.target_id, target.full_name)
        return True

    @staticmethod
    def set_active(session: Session, target_id: int, active: bool) -> bool:
        """Toggle the active status of a target."""
        target = session.get(TargetRegistry, target_id)
        if target is None:
            return False
        target.is_active = active
        session.flush()
        logger.info("Target %s: id=%d", "activated" if active else "deactivated", target_id)
        return True

    @staticmethod
    def count_active(session: Session) -> int:
        """Return the count of active targets."""
        stmt = select(sql_func.count()).where(TargetRegistry.is_active.is_(True))
        return session.execute(stmt).scalar_one()

    # ─── Target Image Methods ───────────────────────────────────────

    @staticmethod
    def add_image(session: Session, image: TargetImage) -> TargetImage:
        """Add an image to a target."""
        session.add(image)
        session.flush()
        logger.info(
            "Image added: id=%d, target_id=%d, order=%d",
            image.image_id, image.target_id, image.image_order,
        )
        return image

    @staticmethod
    def get_images(session: Session, target_id: int) -> list[TargetImage]:
        """Retrieve all images for a target, ordered by image_order."""
        stmt = (
            select(TargetImage)
            .where(TargetImage.target_id == target_id)
            .order_by(TargetImage.image_order)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def delete_image(session: Session, image_id: int) -> bool:
        """Delete a specific target image."""
        image = session.get(TargetImage, image_id)
        if image is None:
            return False
        session.delete(image)
        logger.info("Image deleted: id=%d, target_id=%d", image.image_id, image.target_id)
        return True
