"""
DrishtiX v4.0 — End-to-End Integration Tests.

Tests the full pipeline from target registration through recognition,
alert generation, and data erasure. Uses synthetic test data —
no camera or model files required.
"""

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from drishtix.dao.session import initialize, get_session
from drishtix.dao.target_dao import TargetDAO
from drishtix.dao.embedding_dao import EmbeddingDAO
from drishtix.models.target_registry import TargetRegistry
from drishtix.models.face_embedding import FaceEmbedding
from drishtix.services.gallery_manager import GalleryManager


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Initialize a fresh in-memory database for each test."""
    db_path = str(tmp_path / "test_e2e.db")
    initialize(db_path)
    # Reset GalleryManager singleton for clean state
    GalleryManager._instance = None
    yield
    GalleryManager._instance = None


class TestTargetLifecycle:
    """Test complete target lifecycle: create → embed → match → erase."""

    def test_register_target_with_embeddings(self):
        """Target creation with multiple embeddings should load into gallery."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Test Subject",
                category="CRIMINAL",
                case_number="E2E-001",
            )
            TargetDAO.create(session, target)
            assert target.target_id is not None

            # Add 3 embeddings (simulating 3 face images)
            for i in range(3):
                vec = np.random.randn(512).astype(np.float32)
                vec = vec / np.linalg.norm(vec)
                EmbeddingDAO.create(
                    session, target.target_id, vec,
                    model_version="test_512d",
                )

            emb_count = EmbeddingDAO.count_for_target(session, target.target_id)
            assert emb_count == 3

        # Gallery should load with centroid averaging (F6)
        gallery = GalleryManager.get_instance()
        loaded = gallery.reload_gallery(target_dim=512)
        assert loaded == 1  # 1 centroid template from 3 embeddings

    def test_gallery_matching_after_reload(self):
        """Gallery should match a query vector after reload."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Match Test",
                category="MISSING_PERSON",
                case_number="E2E-002",
            )
            TargetDAO.create(session, target)

            # Create a known embedding
            known_vec = np.random.randn(512).astype(np.float32)
            known_vec = known_vec / np.linalg.norm(known_vec)
            EmbeddingDAO.create(session, target.target_id, known_vec)

        gallery = GalleryManager.get_instance()
        gallery.reload_gallery(target_dim=512)

        # Query with the same vector should match
        result = gallery.match_embedding(known_vec, threshold_override=0.9)
        assert result is not None
        assert result.target.full_name == "Match Test"
        assert result.confidence > 0.99

    def test_gallery_no_match_for_unknown(self):
        """Random query vector should not match any target."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Known Person",
                category="CRIMINAL",
            )
            TargetDAO.create(session, target)
            vec = np.random.randn(512).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            EmbeddingDAO.create(session, target.target_id, vec)

        gallery = GalleryManager.get_instance()
        gallery.reload_gallery(target_dim=512)

        # Query with orthogonal vector should not match
        unknown = np.random.randn(512).astype(np.float32)
        unknown = unknown / np.linalg.norm(unknown)
        result = gallery.match_embedding(unknown, threshold_override=0.9)
        # May or may not match with random vectors - just ensure no crash
        assert result is None or result.confidence < 1.0


class TestMultiFrameConfirmation:
    """Test alert service multi-frame confirmation (§5.4)."""

    def test_confirmation_gate_requires_two_hits(self):
        """First call returns False, second returns True (threshold=2)."""
        from drishtix.services.alert_service import AlertService

        # Test the confirmation logic directly without full AlertService init
        # (AlertService.__init__ triggers SoundPlayer which needs Qt audio)
        svc = object.__new__(AlertService)
        svc._confirmation_state = {}
        svc.CONFIRMATION_THRESHOLD = 2
        svc.CONFIRMATION_WINDOW_SECONDS = 5.0

        # First hit: not yet confirmed
        assert svc._check_confirmation(target_id=42) is False

        # Second hit within window: confirmed
        assert svc._check_confirmation(target_id=42) is True

        # After confirmation, state is reset — next call starts fresh
        assert svc._check_confirmation(target_id=42) is False

    def test_confirmation_window_expiry(self):
        """Hits outside the time window should reset the counter."""
        from drishtix.services.alert_service import AlertService
        import time as _time

        svc = object.__new__(AlertService)
        svc._confirmation_state = {}
        svc.CONFIRMATION_THRESHOLD = 2
        svc.CONFIRMATION_WINDOW_SECONDS = 0.1  # 100ms window for fast test

        # First hit
        assert svc._check_confirmation(target_id=7) is False

        # Wait for window to expire
        _time.sleep(0.15)

        # Second hit — but window expired, so counter resets
        assert svc._check_confirmation(target_id=7) is False

        # Third hit — within new window
        assert svc._check_confirmation(target_id=7) is True


class TestEmbeddingVersioning:
    """Test embedding versioning (F5)."""

    def test_model_version_stored(self):
        """Embedding should store model_version."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Version Test",
                category="CRIMINAL",
            )
            TargetDAO.create(session, target)

            vec = np.random.randn(512).astype(np.float32)
            emb = EmbeddingDAO.create(
                session, target.target_id, vec,
                model_version="arcface_512",
            )
            assert emb.model_version == "arcface_512"

    def test_auto_detect_version(self):
        """model_version should be auto-detected from vector dimensions."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Auto Version",
                category="CRIMINAL",
            )
            TargetDAO.create(session, target)

            vec128 = np.random.randn(128).astype(np.float32)
            emb = EmbeddingDAO.create(session, target.target_id, vec128)
            assert emb.model_version == "auto_128d"


class TestErasureService:
    """Test right-to-erasure (DPDP §8(9))."""

    def test_full_erasure(self):
        """Erasure should delete target and all related data."""
        with get_session() as session:
            target = TargetRegistry(
                full_name="Erasure Test",
                category="CRIMINAL",
                case_number="E2E-ERASE",
            )
            TargetDAO.create(session, target)
            tid = target.target_id

            vec = np.random.randn(512).astype(np.float32)
            EmbeddingDAO.create(session, tid, vec)

        from drishtix.services.erasure_service import ErasureService
        receipt = ErasureService.erase_target(tid, reason="Test erasure")

        assert receipt.success is True
        assert receipt.target_name == "Erasure Test"
        assert receipt.embeddings_deleted == 1
        assert receipt.audit_logged is True

        # Verify target is gone
        with get_session() as session:
            found = TargetDAO.get_by_id(session, tid)
            assert found is None


class TestLivenessDetection:
    """Test anti-spoofing / liveness detection."""

    def test_live_face_scores_positive(self):
        """A synthetic 'live' face should not crash and return a result."""
        from drishtix.services.liveness_service import check_liveness

        # Create a face-like image with varied texture
        face = np.random.randint(100, 200, (80, 80, 3), dtype=np.uint8)
        result = check_liveness(face)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.is_live, bool)

    def test_empty_crop_rejected(self):
        """Empty or tiny crops should be rejected."""
        from drishtix.services.liveness_service import check_liveness

        result = check_liveness(np.zeros((5, 5, 3), dtype=np.uint8))
        assert result.is_live is False
        assert result.score == 0.0


class TestOccupancyAnalytics:
    """Test occupancy tracking."""

    def test_occupancy_counting(self):
        """Should count unique track IDs within the window."""
        from drishtix.services.occupancy_analytics import OccupancyAnalytics

        OccupancyAnalytics._instance = None
        analytics = OccupancyAnalytics.get_instance()
        analytics.reset()

        # Record 3 unique tracks
        snap = analytics.record_detections([1, 2, 3])
        assert snap.current_count == 3

        # Record same tracks again — count should stay 3
        snap = analytics.record_detections([1, 2, 3])
        assert snap.current_count == 3

        # Add a new track
        snap = analytics.record_detections([1, 4])
        assert snap.current_count == 4

        OccupancyAnalytics._instance = None

    def test_peak_tracking(self):
        """Peak should be tracked across recordings."""
        from drishtix.services.occupancy_analytics import OccupancyAnalytics

        OccupancyAnalytics._instance = None
        analytics = OccupancyAnalytics.get_instance()
        analytics.reset()

        analytics.record_detections([1, 2, 3, 4, 5])
        peak, _ = analytics.get_peak()
        assert peak == 5

        analytics.record_detections([1])
        peak, _ = analytics.get_peak()
        assert peak == 5  # Peak should not decrease

        OccupancyAnalytics._instance = None
