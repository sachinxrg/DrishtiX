"""
DrishtiX v4.0 — Recognition Worker (QRunnable).

Asynchronous face embedding extraction and gallery matching executed on a
dedicated QThreadPool worker to keep the camera capture loop running at full FPS.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal

from drishtix.services.alert_service import AlertService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager, MatchResult

logger = logging.getLogger(__name__)


class RecognitionSignals(QObject):
    """Signals emitted by RecognitionWorker."""

    match_completed = Signal(object, tuple)  # MatchResult or None, bbox tuple


class RecognitionWorker(QRunnable):
    """
    Worker task for SFace embedding extraction and gallery matching.
    """

    def __init__(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        raw_detection_row: Optional[np.ndarray],
        recognizer: FaceRecognitionService,
        gallery: GalleryManager,
        alert_service: AlertService,
        camera_id: Optional[int] = None,
        location_tag: str = "Main Camera",
    ) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self.frame = frame.copy()  # Thread-safe copy
        self.bbox = bbox
        self.raw_detection_row = raw_detection_row.copy() if raw_detection_row is not None else None
        self.recognizer = recognizer
        self.gallery = gallery
        self.alert_service = alert_service
        self.camera_id = camera_id
        self.location_tag = location_tag
        self.signals = RecognitionSignals()

    def run(self) -> None:
        """Execute embedding extraction and gallery lookup."""
        try:
            # Step 1: Extract 128-dim embedding
            embedding = self.recognizer.extract_embedding(self.frame, self.raw_detection_row)
            if embedding is None:
                self.signals.match_completed.emit(None, self.bbox)
                return

            # Step 2: Query GalleryManager
            match: Optional[MatchResult] = self.gallery.match_embedding(embedding)

            if match is not None:
                # Step 3: Trigger AlertService (cooldown check, DB, sound, signal)
                self.alert_service.process_match(
                    match=match,
                    frame=self.frame,
                    bbox=self.bbox,
                    camera_id=self.camera_id,
                    location_tag=self.location_tag,
                )

            self.signals.match_completed.emit(match, self.bbox)
        except Exception as e:
            logger.error("RecognitionWorker task failed: %s", e)
            self.signals.match_completed.emit(None, self.bbox)
