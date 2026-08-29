"""
DrishtiX v4.0 — Unified DNN Face Recognition Service.

Provides a unified facade supporting:
1. InsightFace / ArcFace (512-D High-Entropy Embeddings + Demographics for Age-Invariant Recognition)
2. SFace (128-D OpenCV FaceRecognizerSF for Ultra-Lightweight Edge CPU Inference)
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

from drishtix.core.config import get_settings
from drishtix.core.constants import (
    DEFAULT_MATCH_THRESHOLD,
    INSIGHTFACE_DEFAULT_PACK,
    INSIGHTFACE_EMBEDDING_DIM,
    INSIGHTFACE_MATCH_THRESHOLD,
    MODELS_DIR,
    PROJECT_ROOT,
    RECOGNITION_ENGINE_INSIGHTFACE,
    RECOGNITION_ENGINE_SFACE,
    SFACE_EMBEDDING_DIM,
    SFACE_INPUT_SIZE,
    SFACE_MODEL_FILE,
)
from drishtix.services.insightface_service import DemographicInfo, InsightFaceService
from drishtix.utils.vector_math import cosine_similarity, normalize_l2

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """
    Unified Face Recognition Service.
    Wraps InsightFace (ArcFace 512-D) and OpenCV SFace (128-D) behind a thread-safe interface.
    """

    _instance: Optional["FaceRecognitionService"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        engine: Optional[str] = None,
        model_path: Optional[str | Path] = None,
        match_threshold: Optional[float] = None,
        model_pack: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.engine = (engine or settings.recognition.engine or RECOGNITION_ENGINE_SFACE).lower()
        self.model_pack = model_pack or settings.recognition.model_pack or INSIGHTFACE_DEFAULT_PACK

        if match_threshold is not None:
            self.match_threshold = float(match_threshold)
        elif self.engine == RECOGNITION_ENGINE_INSIGHTFACE:
            self.match_threshold = float(INSIGHTFACE_MATCH_THRESHOLD)
        else:
            self.match_threshold = float(settings.recognition.match_threshold or DEFAULT_MATCH_THRESHOLD)

        self._sface_recognizer: Optional[cv2.FaceRecognizerSF] = None
        self._insightface_service: Optional[InsightFaceService] = None
        self._lock = threading.Lock()
        self._model_path = self._resolve_sface_model_path(model_path)

        self._initialize_engines()

    @classmethod
    def get_instance(cls) -> "FaceRecognitionService":
        """Singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def embedding_dim(self) -> int:
        """Return the output vector dimensionality of the active engine."""
        if self.engine == RECOGNITION_ENGINE_INSIGHTFACE and self._insightface_service and self._insightface_service.is_available():
            return INSIGHTFACE_EMBEDDING_DIM
        return SFACE_EMBEDDING_DIM

    def _resolve_sface_model_path(self, custom_path: Optional[str | Path]) -> Optional[Path]:
        """Find the SFace ONNX model on disk."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))

        candidates.extend([
            MODELS_DIR / SFACE_MODEL_FILE,
            PROJECT_ROOT / "models" / SFACE_MODEL_FILE,
            Path("models") / SFACE_MODEL_FILE,
            Path(SFACE_MODEL_FILE),
        ])

        for c in candidates:
            if c.exists():
                return c.resolve()

        return None

    def _initialize_engines(self) -> None:
        """Initialize active and fallback recognition backends."""
        # 1. Initialize SFace (Always available as edge fallback)
        if self._model_path and self._model_path.exists():
            try:
                self._sface_recognizer = cv2.FaceRecognizerSF.create(
                    model=str(self._model_path),
                    config="",
                    backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                    target_id=cv2.dnn.DNN_TARGET_CPU,
                )
                logger.info("SFace backend ready (128-D).")
            except Exception as e:
                logger.warning("Failed to initialize SFace recognizer: %s", e)

        # 2. Initialize InsightFace if requested
        if self.engine == RECOGNITION_ENGINE_INSIGHTFACE:
            try:
                self._insightface_service = InsightFaceService(
                    model_pack=self.model_pack,
                    match_threshold=self.match_threshold,
                )
                if self._insightface_service.is_available():
                    logger.info("InsightFace backend ready (512-D ArcFace + Demographics).")
                else:
                    logger.warning("InsightFace requested but unavailable; falling back to SFace.")
                    self.engine = RECOGNITION_ENGINE_SFACE
            except Exception as e:
                logger.error("InsightFace initialization failed: %s", e)
                self.engine = RECOGNITION_ENGINE_SFACE

    def is_initialized(self) -> bool:
        """Return True if at least one recognition engine is loaded."""
        if self.engine == RECOGNITION_ENGINE_INSIGHTFACE and self._insightface_service and self._insightface_service.is_available():
            return True
        return self._sface_recognizer is not None

    def set_engine(self, engine: str, model_pack: Optional[str] = None) -> None:
        """Switch recognition engine at runtime."""
        with self._lock:
            self.engine = engine.lower()
            if model_pack:
                self.model_pack = model_pack
            self._initialize_engines()

    def align_crop(self, frame: np.ndarray, face_detection_row: np.ndarray) -> Optional[np.ndarray]:
        """Align and crop face using landmark points."""
        if frame is None or face_detection_row is None:
            return None

        if self._sface_recognizer is not None:
            with self._lock:
                try:
                    return self._sface_recognizer.alignCrop(frame, face_detection_row)
                except Exception:
                    pass

        return None

    def extract_embedding(
        self,
        frame: np.ndarray,
        raw_detection_row: Optional[np.ndarray] = None,
    ) -> Optional[np.ndarray]:
        """
        Extract an L2-normalized embedding vector (512-D for InsightFace, 128-D for SFace).
        """
        if frame is None or frame.size == 0:
            return None

        # 1. InsightFace ArcFace (512-D)
        if self.engine == RECOGNITION_ENGINE_INSIGHTFACE and self._insightface_service and self._insightface_service.is_available():
            vec = self._insightface_service.extract_embedding(frame, raw_detection_row)
            if vec is not None:
                return vec

        # 2. SFace (128-D)
        if self._sface_recognizer is not None:
            with self._lock:
                try:
                    if raw_detection_row is not None:
                        try:
                            aligned = self._sface_recognizer.alignCrop(frame, raw_detection_row)
                        except Exception:
                            aligned = None
                        if aligned is None or aligned.size == 0:
                            aligned = cv2.resize(frame, SFACE_INPUT_SIZE)
                    else:
                        if frame.shape[:2] != SFACE_INPUT_SIZE:
                            aligned = cv2.resize(frame, SFACE_INPUT_SIZE)
                        else:
                            aligned = frame

                    feat = self._sface_recognizer.feature(aligned)
                    if feat is not None:
                        vec = feat.flatten().astype(np.float32)
                        return normalize_l2(vec)
                except Exception as e:
                    logger.error("SFace extraction error: %s", e)

        return None

    def extract_embedding_and_demographics(
        self,
        frame: np.ndarray,
        raw_detection_row: Optional[np.ndarray] = None,
    ) -> tuple[Optional[np.ndarray], Optional[DemographicInfo]]:
        """
        Extract embedding and demographics in a single inference pass.

        When InsightFace is active, this avoids the double-inference pattern
        of calling extract_embedding() and estimate_demographics() separately
        (each of which runs the full SCRFD + ArcFace + GenderAge pipeline).

        When SFace is the active engine, demographics are not available, so
        this returns the embedding with None demographics.

        Returns:
            Tuple of (embedding_vector, DemographicInfo) — either may be None.
        """
        if frame is None or frame.size == 0:
            return None, None

        # 1. InsightFace: single-pass combined extraction
        if self.engine == RECOGNITION_ENGINE_INSIGHTFACE and self._insightface_service and self._insightface_service.is_available():
            emb, demo = self._insightface_service.extract_embedding_and_demographics(frame, raw_detection_row)
            if emb is not None:
                return emb, demo

        # 2. SFace fallback: embedding only, no demographics
        emb = self.extract_embedding(frame, raw_detection_row)
        return emb, None

    def estimate_demographics(self, frame: np.ndarray) -> Optional[DemographicInfo]:
        """
        Estimate age and gender from face image.
        Supported when InsightFace engine is active.
        """
        if self._insightface_service and self._insightface_service.is_available():
            return self._insightface_service.estimate_demographics(frame)
        return None

    def match(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        Supports both 128-D and 512-D vectors seamlessly.
        """
        if embedding1 is None or embedding2 is None:
            return 0.0

        return cosine_similarity(embedding1, embedding2)
