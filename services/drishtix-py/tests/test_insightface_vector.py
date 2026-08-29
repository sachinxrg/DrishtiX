"""Unit tests for InsightFace 512-D vector matching, dynamic gallery sizing, and demographic telemetry."""

import numpy as np
from drishtix.core.constants import INSIGHTFACE_EMBEDDING_DIM
from drishtix.models.face_embedding import FaceEmbedding
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager, TargetProfile
from drishtix.services.insightface_service import DemographicInfo
from drishtix.utils.image_utils import draw_tactical_bbox
from drishtix.utils.vector_math import batch_cosine_similarity, cosine_similarity, normalize_l2


def test_512d_normalize_and_similarity():
    """Verify 512-D ArcFace vector normalization and cosine similarity."""
    v1 = np.random.randn(512).astype(np.float32)
    v2 = np.random.randn(512).astype(np.float32)

    v1_norm = normalize_l2(v1)
    v2_norm = normalize_l2(v2)

    assert v1_norm.shape == (512,)
    assert np.isclose(np.linalg.norm(v1_norm), 1.0, atol=1e-5)
    assert np.isclose(np.linalg.norm(v2_norm), 1.0, atol=1e-5)

    # Identical vector similarity should be 1.0
    self_sim = cosine_similarity(v1_norm, v1_norm)
    assert np.isclose(self_sim, 1.0, atol=1e-5)


def test_512d_batch_cosine_similarity():
    """Verify SIMD batch matrix dot product against 50 gallery targets of 512 dimensions."""
    n_targets = 50
    gallery = np.random.randn(n_targets, 512).astype(np.float32)
    for i in range(n_targets):
        gallery[i] = normalize_l2(gallery[i])

    # Target index 17
    query = gallery[17].copy()
    sims = batch_cosine_similarity(query, gallery)

    assert sims.shape == (n_targets,)
    assert np.isclose(sims[17], 1.0, atol=1e-5)
    assert np.argmax(sims) == 17


def test_face_embedding_blob_512d_serialization():
    """Verify FaceEmbedding ORM model transparently stores 512 float32s (2048 bytes)."""
    vec_512 = np.random.randn(512).astype(np.float32)
    vec_512 = normalize_l2(vec_512)

    blob_bytes = FaceEmbedding.from_vector(vec_512)
    assert len(blob_bytes) == 512 * 4  # 2048 bytes

    # Deserialize
    emb = FaceEmbedding(target_id=1, embedding_vector=blob_bytes)
    recovered = emb.get_vector()

    assert recovered.shape == (512,)
    assert np.allclose(recovered, vec_512)


def test_gallery_manager_512d_matching():
    """Verify GalleryManager in-memory matching with a 512-D matrix."""
    gm = GalleryManager(match_threshold=0.45)

    # Manually populate 512-D gallery
    t1 = TargetProfile(
        target_id=101,
        full_name="Aged Suspect Test",
        category="CRIMINAL",
        case_number="FIR-2026-X",
        description="Test 512D",
        profile_image_path=None,
    )
    v1 = normalize_l2(np.random.randn(512).astype(np.float32))

    gm._matrix = v1.reshape(1, 512)
    gm._target_ids = [101]
    gm._embedding_ids = [1]
    gm._targets = {101: t1}

    # Query with identical vector
    match = gm.match_embedding(v1)
    assert match is not None
    assert match.target.target_id == 101
    assert match.target.full_name == "Aged Suspect Test"
    assert np.isclose(match.confidence, 1.0, atol=1e-4)
    assert match.matched_dim == 512


def test_draw_tactical_bbox_demographics():
    """Verify draw_tactical_bbox renders without exception when age and gender are passed."""
    canvas = np.zeros((400, 600, 3), dtype=np.uint8)
    bbox = (50, 50, 120, 150)

    # Should run with no errors
    draw_tactical_bbox(
        frame=canvas,
        bbox=bbox,
        name="Target Name",
        category="CRIMINAL",
        confidence=0.96,
        age=32,
        gender="M",
    )
    assert canvas.any()  # Pixels were modified
