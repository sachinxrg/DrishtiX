"""Integration tests for SQLAlchemy ORM and DAO layers."""

import numpy as np
import pytest

from drishtix.dao.camera_dao import CameraDAO
from drishtix.dao.config_dao import ConfigDAO
from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.dao.session import get_session, initialize, shutdown
from drishtix.dao.target_dao import TargetDAO
from drishtix.models.camera_source import CameraSource
from drishtix.models.detection_log import DetectionLog
from drishtix.models.target_image import TargetImage
from drishtix.models.target_registry import TargetRegistry


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    db_file = tmp_path / "test_drishtix.db"
    initialize(str(db_file))
    yield
    shutdown()


def test_target_crud():
    with get_session() as session:
        # Create
        target = TargetRegistry(
            full_name="Vikram Sharma",
            category="CRIMINAL",
            case_number="FIR-2026-001",
            description="Suspect in robbery",
            profile_image_path="gallery/vikram.jpg",
            is_active=True,
        )
        saved = TargetDAO.create(session, target)
        assert saved.target_id is not None
        target_id = saved.target_id

    with get_session() as session:
        # Read
        found = TargetDAO.get_by_id(session, target_id)
        assert found is not None
        assert found.full_name == "Vikram Sharma"
        assert found.category == "CRIMINAL"

        # Search
        results = TargetDAO.search(session, "Vikram")
        assert len(results) == 1
        assert results[0].target_id == target_id

        # Update
        found.description = "Updated description"
        TargetDAO.update(session, found)

    with get_session() as session:
        updated = TargetDAO.get_by_id(session, target_id)
        assert updated.description == "Updated description"

        # Delete
        deleted = TargetDAO.delete(session, target_id)
        assert deleted is True

    with get_session() as session:
        assert TargetDAO.get_by_id(session, target_id) is None


def test_embedding_and_image_cascade():
    with get_session() as session:
        target = TargetRegistry(
            full_name="Aarav Kumar",
            category="MISSING_PERSON",
            case_number="MIS-9021",
            is_active=True,
        )
        TargetDAO.create(session, target)

        # Add image
        img = TargetImage(
            target_id=target.target_id,
            image_path="gallery/aarav.jpg",
            image_order=0,
        )
        TargetDAO.add_image(session, img)

        # Add 128-dim embedding
        fake_vec = np.ones(128, dtype=np.float32)
        emb = EmbeddingDAO.create(session, target.target_id, fake_vec, source_image_id=img.image_id)
        assert emb.embedding_id is not None

        # Verify retrieval
        loaded_embs = EmbeddingDAO.get_all_for_target(session, target.target_id)
        assert len(loaded_embs) == 1
        assert np.allclose(loaded_embs[0].get_vector(), fake_vec)


def test_detection_log_and_camera():
    with get_session() as session:
        # Camera
        cam = CameraSource(camera_name="Gate 1", source_uri="0", is_active=True)
        CameraDAO.create(session, cam)

        # Target
        target = TargetRegistry(full_name="Test Target", category="CRIMINAL", is_active=True)
        TargetDAO.create(session, target)

        # Detection Log
        log = DetectionLog(
            target_id=target.target_id,
            camera_id=cam.camera_id,
            match_confidence=0.88,
            location_tag="Main Gate",
        )
        DetectionLogDAO.create(session, log)
        assert log.log_id is not None

    with get_session() as session:
        recent = DetectionLogDAO.get_recent(session, limit=10)
        assert len(recent) == 1
        assert recent[0].match_confidence == 0.88
        assert recent[0].target.full_name == "Test Target"


def test_config_dao():
    with get_session() as session:
        ConfigDAO.set_value(session, "alert_cooldown", "45", "Cooldown in seconds")
        val = ConfigDAO.get_value(session, "alert_cooldown")
        assert val == "45"
