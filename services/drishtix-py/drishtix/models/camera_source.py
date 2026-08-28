"""
DrishtiX v4.0 — CameraSource ORM model.

Migrated from: com.drishtix.model.CameraSource (Java)
MongoDB collection: 'camera_sources' → SQLite table: 'camera_source'
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from drishtix.models.base import Base


class CameraSource(Base):
    """
    Camera source entity.

    Represents a connected camera device (USB webcam, integrated laptop camera)
    or a remote video stream (RTSP/HTTP URL). The source_uri field accepts
    either an integer device index (e.g., '0') or a stream URL.
    """

    __tablename__ = "camera_source"

    camera_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_uri: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Device index (int) or RTSP/HTTP URL (string)",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    @property
    def device_index(self) -> int:
        """
        Parse source_uri as an integer device index.

        Returns:
            The device index if source_uri is numeric, otherwise -1
            (indicating an RTSP/URL source).
        """
        try:
            return int(self.source_uri.strip())
        except (ValueError, AttributeError):
            return -1

    @property
    def is_stream(self) -> bool:
        """True if this source is a network stream (not a local device)."""
        return self.device_index == -1

    def __repr__(self) -> str:
        return f"CameraSource(id={self.camera_id}, name='{self.camera_name}', uri='{self.source_uri}')"
