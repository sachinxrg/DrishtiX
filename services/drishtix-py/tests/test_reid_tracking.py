"""Unit tests for Whole-Body Re-Identification, Torso Expansion, and Sensor Fusion Matrix."""

import numpy as np
from drishtix.services.reid_tracking import (
    BODY_EMBEDDING_DIM,
    DnnBodyReIdService,
    SensorFusionEngine,
    expand_face_to_torso_bbox,
    extract_torso_crop,
    normalize_l2,
)


def test_expand_face_to_torso_bbox():
    """Verify face bbox (100, 100, 50, 50) is expanded downwards by 200% and outwards by 20%."""
    face_bbox = (100, 100, 50, 50)
    frame_w, frame_h = 640, 480

    torso_bbox = expand_face_to_torso_bbox(face_bbox, frame_w, frame_h)
    tx, ty, tw, th = torso_bbox

    # Width: 50 + 20% = 60
    assert tw == 60
    # Height: 50 + 200% = 150
    assert th == 150
    # X: centered: 100 - (50 * 0.1) = 95
    assert tx == 95
    # Y: starts at top of face (100)
    assert ty == 100


def test_extract_torso_crop():
    """Verify safe crop extraction with memory bounds protection."""
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    face_bbox = (50, 50, 40, 40)

    res = extract_torso_crop(dummy_frame, face_bbox)
    assert res.is_valid is True
    assert res.torso_image is not None
    assert res.torso_image.shape[0] == 120  # 40 + 200%
    assert res.torso_image.shape[1] == 48   # 40 + 20%


def test_reid_body_embedding_and_matching():
    """Verify OSNet ReID service extracts 512-D embedding and matches in-memory."""
    service = DnnBodyReIdService.get_instance()
    dummy_torso = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)

    emb = service.extract_body_embedding(dummy_torso)
    assert emb is not None
    assert emb.shape == (BODY_EMBEDDING_DIM,)
    assert np.isclose(np.linalg.norm(emb), 1.0, atol=1e-5)

    # Register target
    service.register_target_body(target_id=42, full_name="Suspect Lock Test", body_embedding=emb)

    # Match identical embedding
    match = service.match_body_embedding(emb, threshold_override=0.5)
    assert match is not None
    assert match[0] == 42
    assert match[1] == "Suspect Lock Test"
    assert np.isclose(match[2], 1.0, atol=1e-4)


def test_sensor_fusion_engine_with_landmarks():
    """Verify α=0.8, β=0.2 weighting when landmarks are visible."""
    fusion = SensorFusionEngine.compute_fusion(
        target_id=1,
        full_name="Target A",
        face_confidence=0.90,
        body_confidence=0.80,
        has_facial_landmarks=True,
    )
    # 0.8 * 0.90 + 0.2 * 0.80 = 0.72 + 0.16 = 0.88
    assert np.isclose(fusion.fused_confidence, 0.88, atol=1e-4)
    assert fusion.alpha_weight == 0.80
    assert fusion.beta_weight == 0.20
    assert fusion.landmarks_active is True


def test_sensor_fusion_engine_landmarks_lost():
    """Verify α=0.0, β=1.0 weighting when head is turned >60° or backwards."""
    fusion = SensorFusionEngine.compute_fusion(
        target_id=1,
        full_name="Target A",
        face_confidence=0.90,
        body_confidence=0.85,
        has_facial_landmarks=False,
    )
    # 0.0 * 0.90 + 1.0 * 0.85 = 0.85
    assert np.isclose(fusion.fused_confidence, 0.85, atol=1e-4)
    assert fusion.alpha_weight == 0.00
    assert fusion.beta_weight == 1.00
    assert fusion.landmarks_active is False
