"""
DrishtiX v4.0 — DNN Face Detection Service (YuNet).

Encapsulates OpenCV's FaceDetectorYN (YuNet ONNX model).
Provides high-speed multi-face detection (~2-5ms per frame) with 5-point
facial landmarks for metric alignment in SFace.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from drishtix.core.constants import (
    DEFAULT_NMS_THRESHOLD,
    DEFAULT_SCORE_THRESHOLD,
    MODELS_DIR,
    PROJECT_ROOT,
    YUNET_MODEL_FILE,
)

logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Encapsulates a single detected face from YuNet."""

    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    landmarks: np.ndarray  # 5x2 array of (x, y) coordinates
    raw_row: np.ndarray  # 15-column YuNet output array for SFace alignCrop


class FaceDetectionService:
    """
    YuNet face detection service wrapping cv2.FaceDetectorYN.
    """

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
        top_k: int = 200,
    ) -> None:
        self.score_threshold = float(score_threshold)
        self.nms_threshold = float(nms_threshold)
        self.top_k = top_k
        self._detector: Optional[cv2.FaceDetectorYN] = None
        self._last_size: Tuple[int, int] = (0, 0)
        self._model_path = self._resolve_model_path(model_path)

        self._initialize_detector()

    def _resolve_model_path(self, custom_path: Optional[str | Path]) -> Optional[Path]:
        """Find the YuNet ONNX model on disk."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))

        candidates.extend([
            MODELS_DIR / YUNET_MODEL_FILE,
            PROJECT_ROOT / "models" / YUNET_MODEL_FILE,
            PROJECT_ROOT / "services" / "drishtix-app" / "models" / YUNET_MODEL_FILE,
            Path("models") / YUNET_MODEL_FILE,
            Path(YUNET_MODEL_FILE),
        ])

        for c in candidates:
            if c.exists():
                logger.info("Found YuNet model at: %s", c.resolve())
                return c.resolve()

        logger.warning(
            "YuNet model '%s' not found in standard directories.",
            YUNET_MODEL_FILE,
        )
        return None

    def _initialize_detector(self) -> None:
        """Create the cv2.FaceDetectorYN instance with backend fallbacks."""
        if not self._model_path or not self._model_path.exists():
            logger.warning("YuNet detector initialized in disabled/fallback mode (model missing).")
            return

        initial_size = (320, 320)
        str_path = str(self._model_path)

        # Attempt 1: Default CPU ONNX Runtime backend
        try:
            self._detector = cv2.FaceDetectorYN.create(
                model=str_path,
                config="",
                input_size=initial_size,
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=self.top_k,
                backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                target_id=cv2.dnn.DNN_TARGET_CPU,
            )
            self._last_size = initial_size
            logger.info("YuNet FaceDetectorYN created successfully (CPU backend).")
        except Exception as e:
            logger.error("Failed to create YuNet detector: %s", e)
            self._detector = None

    def is_initialized(self) -> bool:
        """Return True if the YuNet model is loaded and ready."""
        return self._detector is not None

    def set_score_threshold(self, threshold: float) -> None:
        """Update detection confidence threshold at runtime."""
        self.score_threshold = float(threshold)
        if self._detector:
            self._detector.setScoreThreshold(self.score_threshold)

    def set_nms_threshold(self, threshold: float) -> None:
        """Update Non-Maximum Suppression threshold."""
        self.nms_threshold = float(threshold)
        if self._detector:
            self._detector.setNMSThreshold(self.nms_threshold)

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect all faces in the given frame using YuNet.

        Args:
            frame: Input BGR image (H, W, 3).

        Returns:
            List of FaceDetection objects.
        """
        if self._detector is None or frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        if (w, h) != self._last_size:
            self._detector.setInputSize((w, h))
            self._last_size = (w, h)

        try:
            _, faces = self._detector.detect(frame)
            if faces is None or len(faces) == 0:
                return []

            results: List[FaceDetection] = []
            for row in faces:
                # Format: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rm, y_rm, x_lm, y_lm, score]
                x = max(0, int(round(row[0])))
                y = max(0, int(round(row[1])))
                width = int(round(row[2]))
                height = int(round(row[3]))
                score = float(row[14])

                # Confidence check
                if score < self.score_threshold:
                    continue

                # Boundary clamping
                if x + width > w:
                    width = w - x
                if y + height > h:
                    height = h - y

                # Geometric validation: minimum face size and realistic human face aspect ratio
                if width < 35 or height < 35:
                    continue

                aspect_ratio = width / float(height)
                if aspect_ratio < 0.55 or aspect_ratio > 1.7:
                    continue

                # Extract 5 landmarks
                landmarks = np.array(
                    [
                        [row[4], row[5]],  # Right eye
                        [row[6], row[7]],  # Left eye
                        [row[8], row[9]],  # Nose tip
                        [row[10], row[11]],  # Right mouth corner
                        [row[12], row[13]],  # Left mouth corner
                    ],
                    dtype=np.float32,
                )

                results.append(
                    FaceDetection(
                        bbox=(x, y, width, height),
                        confidence=score,
                        landmarks=landmarks,
                        raw_row=row.copy(),
                    )
                )

            # Secondary Non-Maximum Suppression to prevent duplicate boxes on the same face
            filtered_results = self._apply_nms(results, iou_threshold=0.3)
            return filtered_results
        except Exception as e:
            logger.error("Error during YuNet face detection: %s", e)
            return []

    def _apply_nms(self, detections: List[FaceDetection], iou_threshold: float = 0.3) -> List[FaceDetection]:
        """Suppresses overlapping bounding boxes, keeping highest confidence."""
        if len(detections) <= 1:
            return detections

        # Sort by confidence descending
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        keep: List[FaceDetection] = []

        for det in sorted_dets:
            overlap = False
            for k in keep:
                if self._calculate_iou(det.bbox, k.bbox) > iou_threshold:
                    overlap = True
                    break
            if not overlap:
                keep.append(det)

        return keep

    @staticmethod
    def _calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
        """Calculate IoU between two (x, y, w, h) boxes."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h

        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]
        union_area = boxAArea + boxBArea - inter_area

        if union_area <= 0:
            return 0.0
        return inter_area / float(union_area)
