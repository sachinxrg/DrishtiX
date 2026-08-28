"""Data Access Object (DAO) package — Repository pattern for database operations."""

from drishtix.dao.session import (
    initialize,
    get_session,
    get_engine,
    test_connection,
    shutdown,
)
from drishtix.dao.target_dao import TargetDAO
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.camera_dao import CameraDAO
from drishtix.dao.config_dao import ConfigDAO
from drishtix.dao.audit_dao import AuditDAO

__all__ = [
    "initialize",
    "get_session",
    "get_engine",
    "test_connection",
    "shutdown",
    "TargetDAO",
    "EmbeddingDAO",
    "DetectionLogDAO",
    "CameraDAO",
    "ConfigDAO",
    "AuditDAO",
]
