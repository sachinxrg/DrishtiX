"""
DrishtiX v4.0 — Whole-Body Re-Identification & Sensor Fusion Service.

Implements deep body feature extraction (OSNet 512-D embeddings), mathematical
torso/clothing expansion, hardware delegate routing (OpenVINO / TensorRT / CUDA / CPU),
and real-time identity sensor fusion matrix:
    E_fused = α · E_face + β · E_body

Off-Heap Memory Safety:
- Explicit scoping and NumPy buffer management.
- Zero-copy tensor conversion where applicable.
- Mutex-guarded thread-safe inference pools.
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ─── Constants & Defaults ──────────────────────────────────────────────────
BODY_EMBEDDING_DIM = 512
REID_INPUT_SIZE = (128, 256)  # Standard ReID input (width=128, height=256)
DEFAULT_BODY_MATCH_THRESHOLD = 0.60

# Expansion Factors for Facial-to-Spatial Torso Handoff
EXPANSION_DOWN_RATIO = 2.00  # Expand downwards by 200% (captures neck, shoulders, torso)
EXPANSION_OUT_RATIO = 0.20   # Expand outwards horizontally by 20% (captures clothing silhouette)


@dataclass
class TorsoCropResult:
    """Result of mathematical bounding box expansion and safe extraction."""

    torso_bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    torso_image: Optional[np.ndarray]      # Cropped BGR Mat
    is_valid: bool


@dataclass
class BodyReIdProfile:
    """In-memory body profile of an active or registered target."""

    target_id: int
    full_name: str
    body_embedding: np.ndarray             # 512-D float32 L2-normalized vector
    clothing_tag: Optional[str] = None
    last_seen_timestamp: float = 0.0


@dataclass
class FusionMatchResult:
    """Unified identity result calculated via the weighted sensor fusion matrix."""

    target_id: int
    full_name: str
    fused_confidence: float
    face_confidence: float
    body_confidence: float
    alpha_weight: float
    beta_weight: float
    landmarks_active: bool


# ─── Vector Utilities ──────────────────────────────────────────────────────
def normalize_l2(vector: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """L2-normalize a 1D float32 vector in-place or via copy."""
    norm = np.linalg.norm(vector)
    if norm < eps:
        return vector
    return (vector / norm).astype(np.float32)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two normalized vectors."""
    if v1 is None or v2 is None or v1.size == 0 or v2.size == 0:
        return 0.0
    dot_product = float(np.dot(v1.flatten(), v2.flatten()))
    return max(0.0, min(1.0, dot_product))


# ─── Bounding Box Torso Expansion ──────────────────────────────────────────
def expand_face_to_torso_bbox(
    face_bbox: Sequence[int],
    frame_width: int,
    frame_height: int,
    down_ratio: float = EXPANSION_DOWN_RATIO,
    out_ratio: float = EXPANSION_OUT_RATIO,
) -> Tuple[int, int, int, int]:
    """
    Mathematically expand face bounding box downwards by 200% and outwards by 20%
    to capture the target's neck, shoulders, and upper torso (clothing profile).

    Args:
        face_bbox: (x, y, w, h) face bounding box.
        frame_width: Image width limit.
        frame_height: Image height limit.
        down_ratio: Vertical downward multiplier (default: 2.0 = 200%).
        out_ratio: Horizontal outward multiplier (default: 0.2 = 20%).

    Returns:
        (x_body, y_body, w_body, h_body) clipped to frame boundaries.
    """
    fx, fy, fw, fh = [int(v) for v in face_bbox]

    # Calculate horizontal expansion
    horizontal_pad = int(fw * (out_ratio / 2.0))
    bx = max(0, fx - horizontal_pad)
    bw = fw + (2 * horizontal_pad)

    # Calculate vertical expansion (start from upper forehead, stretch down past torso)
    by = max(0, fy)
    bh = int(fh + (fh * down_ratio))

    # Strict clamping to native frame boundaries
    bx = max(0, min(bx, frame_width - 1))
    by = max(0, min(by, frame_height - 1))
    bw = max(1, min(bw, frame_width - bx))
    bh = max(1, min(bh, frame_height - by))

    return (bx, by, bw, bh)


def extract_torso_crop(
    frame: np.ndarray,
    face_bbox: Sequence[int],
) -> TorsoCropResult:
    """
    Safely crop the expanded torso region from a native OpenCV Mat with boundary guards.
    """
    if frame is None or frame.size == 0:
        return TorsoCropResult(torso_bbox=(0, 0, 0, 0), torso_image=None, is_valid=False)

    img_h, img_w = frame.shape[:2]
    torso_bbox = expand_face_to_torso_bbox(face_bbox, img_w, img_h)
    tx, ty, tw, th = torso_bbox

    if tw <= 4 or th <= 4:
        return TorsoCropResult(torso_bbox=torso_bbox, torso_image=None, is_valid=False)

    try:
        # Explicit copy to isolate memory from parent frame buffer
        torso_crop = frame[ty : ty + th, tx : tx + tw].copy()
        return TorsoCropResult(torso_bbox=torso_bbox, torso_image=torso_crop, is_valid=True)
    except Exception as e:
        logger.debug("Failed to extract torso crop: %s", e)
        return TorsoCropResult(torso_bbox=torso_bbox, torso_image=None, is_valid=False)


# ─── OSNet Whole-Body Re-ID Service ────────────────────────────────────────
class DnnBodyReIdService:
    """
    Whole-Body Person Re-Identification Service.

    Extracts 512-dimensional metric embeddings from body crops using an OSNet
    (Omni-Scale Network) backbone. Supports hardware acceleration via:
    1. NVIDIA TensorRT / CUDA
    2. Intel OpenVINO (iGPU / NPU / CPU)
    3. ONNX Runtime / OpenCV DNN fallback
    """

    _instance: Optional["DnnBodyReIdService"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        match_threshold: float = DEFAULT_BODY_MATCH_THRESHOLD,
    ) -> None:
        self.match_threshold = float(match_threshold)
        self._lock = threading.Lock()
        self._initialized = False
        self._net: Optional[cv2.dnn.Net] = None
        self._ort_session = None
        self._body_gallery: Dict[int, BodyReIdProfile] = {}
        self._model_path = self._resolve_model_path(model_path)

        self._initialize_hardware_delegate()

    @classmethod
    def get_instance(cls) -> "DnnBodyReIdService":
        """Thread-safe singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _resolve_model_path(self, custom_path: Optional[Union[str, Path]]) -> Optional[Path]:
        """Find the OSNet ONNX model weight file on disk."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))

        base_dirs = [
            Path("models"),
            Path("services/drishtix-py/models"),
            Path(__file__).resolve().parent.parent / "models",
            Path(__file__).resolve().parent.parent.parent / "models",
        ]

        model_names = [
            "osnet_x1_0.onnx",
            "osnet_x0_25_msmt17.onnx",
            "osnet_ain_x1_0.onnx",
            "reid_osnet_512.onnx",
        ]

        for d in base_dirs:
            for name in model_names:
                candidates.append(d / name)

        for c in candidates:
            if c.exists():
                logger.info("Found OSNet Re-ID model at: %s", c.resolve())
                return c.resolve()

        return None

    def _initialize_hardware_delegate(self) -> None:
        """
        Configure execution backend prioritizing OpenVINO, CUDA/TensorRT, then CPU.
        If the model file is missing, attempts an automatic download first.
        """
        if not self._model_path or not self._model_path.exists():
            # Attempt auto-download of OSNet model (O8/B12)
            try:
                from drishtix.scripts.download_osnet import ensure_osnet_model
                downloaded_path = ensure_osnet_model()
                if downloaded_path.exists():
                    self._model_path = downloaded_path
                    logger.info("OSNet model auto-downloaded to: %s", downloaded_path)
            except Exception as e:
                logger.warning("OSNet auto-download failed: %s", e)

        if not self._model_path or not self._model_path.exists():
            logger.warning("OSNet ONNX model not found. Initialized in lightweight synthetic mode.")
            self._initialized = True
            return

        model_str = str(self._model_path)

        # 1. Attempt OpenCV DNN with Hardware Acceleration
        try:
            net = cv2.dnn.readNetFromONNX(model_str)

            # Check for NVIDIA CUDA / TensorRT
            has_cuda = cv2.cuda.getCudaEnabledDeviceCount() > 0 if hasattr(cv2, "cuda") else False
            if has_cuda:
                try:
                    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                    logger.info("OSNet Re-ID configured with NVIDIA CUDA delegate.")
                    self._net = net
                    self._initialized = True
                    return
                except Exception as e:
                    logger.warning("CUDA delegate failed: %s. Attempting OpenVINO.", e)

            # Check for Intel OpenVINO
            try:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                logger.info("OSNet Re-ID configured with Intel OpenVINO delegate.")
                self._net = net
                self._initialized = True
                return
            except Exception:
                pass

            # Fallback to standard optimized CPU
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            self._net = net
            self._initialized = True
            logger.info("OSNet Re-ID configured with OpenCV DNN CPU fallback.")
            return

        except Exception as e:
            logger.warning("OpenCV DNN initialization failed: %s. Attempting ONNX Runtime.", e)

        # 2. Attempt ONNX Runtime Session
        try:
            import onnxruntime as ort

            available_providers = ort.get_available_providers()
            providers = []
            if "CUDAExecutionProvider" in available_providers:
                providers.append("CUDAExecutionProvider")
            if "OpenVINOExecutionProvider" in available_providers:
                providers.append("OpenVINOExecutionProvider")
            providers.append("CPUExecutionProvider")

            self._ort_session = ort.InferenceSession(model_str, providers=providers)
            self._initialized = True
            logger.info("OSNet Re-ID initialized via ONNX Runtime with providers: %s", providers)
        except Exception as ex:
            logger.error("All hardware delegate backends failed: %s", ex)
            self._initialized = True  # Runs fallback feature generator

    def is_available(self) -> bool:
        """Check if Re-ID service is ready for inference."""
        return self._initialized

    def extract_body_embedding(self, torso_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract a 512-dimensional L2-normalized feature embedding (E_body) from a torso crop.
        Ensures complete off-heap memory safety and bounds protection.
        """
        if torso_image is None or torso_image.size == 0:
            return None

        with self._lock:
            try:
                # Preprocessing: Standard Re-ID ImageNet Normalization
                resized = cv2.resize(torso_image, REID_INPUT_SIZE, interpolation=cv2.INTER_LINEAR)
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

                # 1. OpenCV DNN Inference Path
                if self._net is not None:
                    # Blob: 1x3x256x128, Scaled by 1/255, ImageNet Mean subtraction
                    blob = cv2.dnn.blobFromImage(
                        rgb,
                        scalefactor=1.0 / 255.0,
                        size=REID_INPUT_SIZE,
                        mean=(0.485 * 255, 0.456 * 255, 0.406 * 255),
                        swapRB=False,
                        crop=False,
                    )
                    # Std division
                    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)
                    blob = blob / std

                    self._net.setInput(blob)
                    feat = self._net.forward()
                    del blob  # Explicit off-heap release
                    vec = feat.flatten().astype(np.float32)
                    return normalize_l2(vec)

                # 2. ONNX Runtime Inference Path
                if self._ort_session is not None:
                    img_tensor = rgb.astype(np.float32) / 255.0
                    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                    normalized = (img_tensor - mean) / std
                    transposed = np.transpose(normalized, (2, 0, 1))  # (3, 256, 128)
                    input_batch = np.expand_dims(transposed, axis=0)  # (1, 3, 256, 128)

                    input_name = self._ort_session.get_inputs()[0].name
                    outputs = self._ort_session.run(None, {input_name: input_batch})
                    vec = outputs[0].flatten().astype(np.float32)
                    return normalize_l2(vec)

                # 3. Fallback High-Density Visual Feature Generator
                # Generates deterministic 512-D spatial-chromatic signature for testing
                gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
                hsv = cv2.cvtColor(resized, cv2.COLOR_RGB2HSV)
                h_hist = cv2.calcHist([hsv], [0], None, [128], [0, 180]).flatten()
                s_hist = cv2.calcHist([hsv], [1], None, [128], [0, 256]).flatten()
                combined = np.concatenate([hist, h_hist, s_hist]).astype(np.float32)
                return normalize_l2(combined[:BODY_EMBEDDING_DIM])

            except Exception as e:
                logger.error("Body embedding extraction failed: %s", e)
                return None

    def register_target_body(
        self,
        target_id: int,
        full_name: str,
        body_embedding: np.ndarray,
        clothing_tag: Optional[str] = None,
    ) -> None:
        """Register or update an active target's body profile in memory."""
        with self._lock:
            self._body_gallery[target_id] = BodyReIdProfile(
                target_id=target_id,
                full_name=full_name,
                body_embedding=normalize_l2(body_embedding),
                clothing_tag=clothing_tag,
            )

    def match_body_embedding(
        self,
        query_embedding: np.ndarray,
        threshold_override: Optional[float] = None,
    ) -> Optional[Tuple[int, str, float]]:
        """
        Search in-memory body gallery for the closest matching identity.

        Returns:
            (target_id, full_name, similarity_score) or None if below threshold.
        """
        if query_embedding is None or not self._body_gallery:
            return None

        thresh = threshold_override if threshold_override is not None else self.match_threshold
        best_id: Optional[int] = None
        best_name = ""
        best_score = 0.0

        with self._lock:
            for tid, profile in self._body_gallery.items():
                score = cosine_similarity(query_embedding, profile.body_embedding)
                if score > best_score:
                    best_score = score
                    best_id = tid
                    best_name = profile.full_name

        if best_id is not None and best_score >= thresh:
            return (best_id, best_name, best_score)

        return None


# ─── Sensor Fusion Weighted Matrix ─────────────────────────────────────────
class SensorFusionEngine:
    """
    Unifies facial and whole-body feature streams dynamically:
        E_fused = α · E_face + β · E_body

    Dynamic Weighting Policy:
    - Normal (Landmarks visible): α = 0.8, β = 0.2
    - Occluded / Turned (>60°):   α = 0.0, β = 1.0 (retains visual lock-on)
    """

    @staticmethod
    def compute_fusion(
        target_id: int,
        full_name: str,
        face_confidence: Optional[float],
        body_confidence: Optional[float],
        has_facial_landmarks: bool,
    ) -> FusionMatchResult:
        """
        Calculate weighted identity confidence based on sensor availability.
        """
        f_conf = float(face_confidence) if face_confidence is not None else 0.0
        b_conf = float(body_confidence) if body_confidence is not None else 0.0

        # Determine dynamic weights
        if has_facial_landmarks and f_conf > 0.0:
            alpha = 0.80
            beta = 0.20
        else:
            # Face turned past 60°, backwards, or occluded
            alpha = 0.00
            beta = 1.00

        # Weighted calculation
        if alpha == 0.0:
            fused_score = b_conf
        elif b_conf == 0.0:
            fused_score = f_conf
        else:
            fused_score = (alpha * f_conf) + (beta * b_conf)

        return FusionMatchResult(
            target_id=target_id,
            full_name=full_name,
            fused_confidence=round(fused_score, 4),
            face_confidence=round(f_conf, 4),
            body_confidence=round(b_conf, 4),
            alpha_weight=alpha,
            beta_weight=beta,
            landmarks_active=has_facial_landmarks,
        )
