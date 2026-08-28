"""
DrishtiX v4.0 — DNN Face Recognition Service (SFace).

Encapsulates OpenCV's FaceRecognizerSF (SFace ONNX model).
Extracts 128-dimensional L2-normalized metric embeddings from aligned
112×112 face crops.
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Sequence

import cv2
import numpy as np

from drishtix.core.constants import (
    DEFAULT_MATCH_THRESHOLD,
    MODELS_DIR,
    PROJECT_ROOT,
    SFACE_EMBEDDING_DIM,
    SFACE_INPUT_SIZE,
    SFACE_MODEL_FILE,
)
from drishtix.utils.vector_math import cosine_similarity, normalize_l2

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """
    SFace face recognition service wrapping cv2.FaceRecognizerSF.
    Thread-safe implementation protected by mutex.
    """

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
    ) -> None:
        self.match_threshold = float(match_threshold)
        self._recognizer: Optional[cv2.FaceRecognizerSF] = None
        self._lock = threading.Lock()
        self._model_path = self._resolve_model_path(model_path)

        self._initialize_recognizer()

    def _resolve_model_path(self, custom_path: Optional[str | Path]) -> Optional[Path]:
        """Find the SFace ONNX model on disk."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))

        candidates.extend([
            MODELS_DIR / SFACE_MODEL_FILE,
            PROJECT_ROOT / "models" / SFACE_MODEL_FILE,
            PROJECT_ROOT / "services" / "drishtix-app" / "models" / SFACE_MODEL_FILE,
            Path("models") / SFACE_MODEL_FILE,
            Path(SFACE_MODEL_FILE),
        ])

        for c in candidates:
            if c.exists():
                logger.info("Found SFace model at: %s", c.resolve())
                return c.resolve()

        logger.warning(
            "SFace model '%s' not found in standard directories.",
            SFACE_MODEL_FILE,
        )
        return None

    def _initialize_recognizer(self) -> None:
        """Create the cv2.FaceRecognizerSF instance."""
        if not self._model_path or not self._model_path.exists():
            logger.warning("SFace recognizer initialized in disabled/fallback mode (model missing).")
            return

        str_path = str(self._model_path)
        try:
            self._recognizer = cv2.FaceRecognizerSF.create(
                model=str_path,
                config="",
                backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                target_id=cv2.dnn.DNN_TARGET_CPU,
            )
            logger.info("SFace FaceRecognizerSF created successfully (CPU backend).")
        except Exception as e:
            logger.error("Failed to create SFace recognizer: %s", e)
            self._recognizer = None

    def is_initialized(self) -> bool:
        """Return True if the SFace model is loaded."""
        return self._recognizer is not None

    def align_crop(self, frame: np.ndarray, face_detection_row: np.ndarray) -> Optional[np.ndarray]:
        """
        Align and crop the face region into a 112×112 normalized image using landmarks.
        """
        if self._recognizer is None or frame is None or face_detection_row is None:
            return None

        with self._lock:
            try:
                aligned_face = self._recognizer.alignCrop(frame, face_detection_row)
                return aligned_face
            except Exception as e:
                logger.debug("SFace alignCrop failed: %s", e)
                return None

    def extract_embedding(
        self,
        frame: np.ndarray,
        raw_detection_row: Optional[np.ndarray] = None,
    ) -> Optional[np.ndarray]:
        """
        Extract a 128-dimensional normalized embedding vector.
        Thread-safe execution.
        """
        if self._recognizer is None or frame is None or frame.size == 0:
            return None

        with self._lock:
            try:
                if raw_detection_row is not None:
                    try:
                        aligned = self._recognizer.alignCrop(frame, raw_detection_row)
                    except Exception:
                        aligned = None
                    if aligned is None or aligned.size == 0:
                        aligned = cv2.resize(frame, SFACE_INPUT_SIZE)
                else:
                    if frame.shape[:2] != SFACE_INPUT_SIZE:
                        aligned = cv2.resize(frame, SFACE_INPUT_SIZE)
                    else:
                        aligned = frame

                # SFace feature extraction
                feat = self._recognizer.feature(aligned)
                if feat is None:
                    return None

                # Flatten to 1D array of 128 float32s
                vec = feat.flatten().astype(np.float32)
                # Ensure L2 normalized
                vec = normalize_l2(vec)
                return vec
            except Exception as e:
                logger.error("Embedding extraction failed: %s", e)
                return None

    def match(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Returns:
            Cosine score (typically 0.0 to 1.0).
        """
        if self._recognizer is not None:
            try:
                # SFace match type: FR_COSINE (0) or FR_NORM_L2 (1)
                score = self._recognizer.match(
                    embedding1.reshape(1, -1),
                    embedding2.reshape(1, -1),
                    cv2.FaceRecognizerSF_FR_COSINE,
                )
                return float(score)
            except Exception:
                pass

        # Fallback to NumPy cosine similarity
        return cosine_similarity(embedding1, embedding2)
