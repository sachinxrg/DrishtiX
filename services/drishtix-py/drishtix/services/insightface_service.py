"""
DrishtiX v4.0 — InsightFace Recognition Service (ArcFace 512-D + SCRFD + GenderAge).

Provides deep craniofacial feature extraction (512-dimensional L2-normalized embeddings)
and demographic estimation (age + gender) using deep convolutional backbones (ArcFace / IResNet).
Enables age-invariant face verification across multi-year intervals (AgeDB-30 benchmark: 98.28%).
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from drishtix.core.constants import (
    INSIGHTFACE_DEFAULT_PACK,
    INSIGHTFACE_EMBEDDING_DIM,
    INSIGHTFACE_MATCH_THRESHOLD,
    PROJECT_ROOT,
)
from drishtix.utils.vector_math import cosine_similarity, normalize_l2

logger = logging.getLogger(__name__)


@dataclass
class DemographicInfo:
    """Demographic metadata predicted from facial features."""

    age: int
    gender: str          # "M" or "F"
    gender_confidence: float = 1.0


@dataclass
class InsightFaceMatch:
    """Full face analysis result from InsightFace."""

    bbox: Tuple[int, int, int, int]    # (x1, y1, x2, y2)
    confidence: float
    landmarks: Optional[np.ndarray]     # (5, 2) or (106, 2)
    embedding: Optional[np.ndarray]     # 512-D float32
    demographics: Optional[DemographicInfo]


class InsightFaceService:
    """
    Enterprise-grade Face Recognition service wrapping InsightFace.
    Thread-safe implementation protected by mutex lock.
    """

    _instance: Optional["InsightFaceService"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        model_pack: str = INSIGHTFACE_DEFAULT_PACK,
        match_threshold: float = INSIGHTFACE_MATCH_THRESHOLD,
        providers: Optional[List[str]] = None,
    ) -> None:
        self.model_pack = model_pack
        self.match_threshold = float(match_threshold)
        self.providers = providers or ["CPUExecutionProvider"]
        self._app = None
        self._lock = threading.Lock()
        self._initialized = False

        self._initialize_app()

    @classmethod
    def get_instance(cls) -> "InsightFaceService":
        """Singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _initialize_app(self) -> None:
        """Initialize the InsightFace FaceAnalysis pipeline."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            # Prepare root models directory
            models_root = str(PROJECT_ROOT / "models" / "insightface")
            Path(models_root).mkdir(parents=True, exist_ok=True)

            logger.info("Initializing InsightFace with model pack '%s'...", self.model_pack)
            self._app = FaceAnalysis(
                name=self.model_pack,
                root=models_root,
                providers=self.providers,
                allowed_modules=["detection", "recognition", "genderage"],
            )
            # Standard inference detection size: 640x640
            self._app.prepare(ctx_id=0, det_size=(640, 640))
            self._initialized = True
            logger.info("InsightFace FaceAnalysis engine successfully initialized.")
        except ImportError:
            logger.warning("InsightFace library is not installed. Running in fallback mode.")
            self._initialized = False
        except Exception as e:
            logger.error("Failed to initialize InsightFace engine: %s", e)
            self._initialized = False

    def is_available(self) -> bool:
        """Return True if InsightFace is initialized and ready."""
        return self._initialized and self._app is not None

    def analyze_frame(self, frame: np.ndarray) -> List[InsightFaceMatch]:
        """
        Detect all faces and extract 512-D embeddings + age/gender for each face.
        """
        if not self.is_available() or frame is None or frame.size == 0:
            return []

        results: List[InsightFaceMatch] = []
        with self._lock:
            try:
                faces = self._app.get(frame)
                for f in faces:
                    bbox_coords = tuple(map(int, f.bbox)) if hasattr(f, "bbox") else (0, 0, 0, 0)
                    det_score = float(f.det_score) if hasattr(f, "det_score") else 0.0
                    kps = f.kps if hasattr(f, "kps") else None

                    emb = None
                    if hasattr(f, "embedding") and f.embedding is not None:
                        emb = normalize_l2(f.embedding.flatten().astype(np.float32))

                    demographics = None
                    if hasattr(f, "age") and hasattr(f, "gender"):
                        gender_str = "M" if f.gender == 1 else "F"
                        demographics = DemographicInfo(
                            age=int(f.age),
                            gender=gender_str,
                            gender_confidence=1.0,
                        )

                    results.append(
                        InsightFaceMatch(
                            bbox=bbox_coords,
                            confidence=det_score,
                            landmarks=kps,
                            embedding=emb,
                            demographics=demographics,
                        )
                    )
            except Exception as e:
                logger.error("InsightFace frame analysis failed: %s", e)

        return results

    def extract_embedding(
        self,
        frame: np.ndarray,
        raw_detection_row: Optional[np.ndarray] = None,
    ) -> Optional[np.ndarray]:
        """
        Extract a 512-dimensional normalized embedding vector from a cropped or full frame.
        """
        if not self.is_available() or frame is None or frame.size == 0:
            return None

        with self._lock:
            try:
                faces = self._app.get(frame)
                if not faces:
                    return None

                # Choose the largest / most confident face
                best_face = max(faces, key=lambda f: f.det_score if hasattr(f, "det_score") else 0.0)
                if hasattr(best_face, "embedding") and best_face.embedding is not None:
                    vec = best_face.embedding.flatten().astype(np.float32)
                    return normalize_l2(vec)
            except Exception as e:
                logger.error("InsightFace embedding extraction failed: %s", e)

        return None

    def extract_embedding_and_demographics(
        self,
        frame: np.ndarray,
        raw_detection_row: Optional[np.ndarray] = None,
    ) -> Tuple[Optional[np.ndarray], Optional[DemographicInfo]]:
        """
        Extract both embedding and demographics in a single inference pass.

        InsightFace's FaceAnalysis.get() computes detection, embedding, and
        demographics all at once. This method avoids the double-inference
        pattern of calling extract_embedding() + estimate_demographics()
        separately — each of which would run the full pipeline independently.

        Returns:
            Tuple of (embedding_vector, demographics) — either may be None.
        """
        if not self.is_available() or frame is None or frame.size == 0:
            return None, None

        with self._lock:
            try:
                faces = self._app.get(frame)
                if not faces:
                    return None, None

                best_face = max(faces, key=lambda f: f.det_score if hasattr(f, "det_score") else 0.0)

                # Extract embedding
                emb = None
                if hasattr(best_face, "embedding") and best_face.embedding is not None:
                    emb = normalize_l2(best_face.embedding.flatten().astype(np.float32))

                # Extract demographics
                demographics = None
                if hasattr(best_face, "age") and hasattr(best_face, "gender"):
                    gender_str = "M" if best_face.gender == 1 else "F"
                    demographics = DemographicInfo(age=int(best_face.age), gender=gender_str)

                return emb, demographics
            except Exception as e:
                logger.error("InsightFace combined extraction failed: %s", e)

        return None, None

    def estimate_demographics(
        self,
        frame: np.ndarray,
    ) -> Optional[DemographicInfo]:
        """
        Estimate age and gender from a facial frame.
        """
        if not self.is_available() or frame is None or frame.size == 0:
            return None

        with self._lock:
            try:
                faces = self._app.get(frame)
                if not faces:
                    return None

                best_face = max(faces, key=lambda f: f.det_score if hasattr(f, "det_score") else 0.0)
                if hasattr(best_face, "age") and hasattr(best_face, "gender"):
                    gender_str = "M" if best_face.gender == 1 else "F"
                    return DemographicInfo(age=int(best_face.age), gender=gender_str)
            except Exception as e:
                logger.debug("Demographics estimation failed: %s", e)

        return None

    def match(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two 512-D embeddings.
        """
        return cosine_similarity(embedding1, embedding2)
