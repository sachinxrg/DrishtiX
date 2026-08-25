"""
DrishtiX v4.0 — Camera DAO.

Repository for CameraSource CRUD operations.
Migrated from: com.drishtix.dao.CameraSourceDAO (Java)
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from drishtix.models.camera_source import CameraSource

logger = logging.getLogger(__name__)


class CameraDAO:
    """Repository for CameraSource database operations."""

    @staticmethod
    def get_all(session: Session, active_only: bool = False) -> list[CameraSource]:
        """
        Retrieve all camera sources, optionally filtered by active status.

        Args:
            session: SQLAlchemy session.
            active_only: If True, return only active cameras.

        Returns:
            List of CameraSource entities.
        """
        stmt = select(CameraSource).order_by(CameraSource.camera_name)
        if active_only:
            stmt = stmt.where(CameraSource.is_active.is_(True))
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(session: Session, camera_id: int) -> Optional[CameraSource]:
        """Retrieve a camera by its ID."""
        return session.get(CameraSource, camera_id)

    @staticmethod
    def create(session: Session, camera: CameraSource) -> CameraSource:
        """Insert a new camera source."""
        session.add(camera)
        session.flush()
        logger.info(
            "Camera created: id=%d, name='%s', uri='%s'",
            camera.camera_id,
            camera.camera_name,
            camera.source_uri,
        )
        return camera

    @staticmethod
    def update(session: Session, camera: CameraSource) -> CameraSource:
        """Update an existing camera source."""
        merged = session.merge(camera)
        session.flush()
        logger.info("Camera updated: id=%d, name='%s'", merged.camera_id, merged.camera_name)
        return merged

    @staticmethod
    def delete(session: Session, camera_id: int) -> bool:
        """Delete a camera source."""
        camera = session.get(CameraSource, camera_id)
        if camera is None:
            return False
        session.delete(camera)
        logger.info("Camera deleted: id=%d", camera_id)
        return True

    @staticmethod
    def set_active(session: Session, camera_id: int, active: bool) -> bool:
        """Toggle active state of a camera."""
        camera = session.get(CameraSource, camera_id)
        if camera is None:
            return False
        camera.is_active = active
        session.flush()
        return True
