"""
DrishtiX v4.0 — Recognition Worker (QRunnable).

Asynchronous face embedding extraction and gallery matching executed on a
dedicated QThreadPool worker to keep the camera capture loop running at full FPS.
Invokes direct thread-safe callbacks to instantly update tracking identities.
"""

import logging
from typing import Callable, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal

from drishtix.services.alert_service import AlertService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.gallery_manager import GalleryManager, MatchResult

logger = logging.getLogger(__name__)


class RecognitionSignals(QObject):
    """Signals emitted by RecognitionWorker."""

    match_completed = Signal(object, tuple, object, object)


class RecognitionWorker(QRunnable):
    """
    Worker task for face embedding extraction, demographic estimation, and gallery matching.
    Supports direct callback invocation for zero-latency identity synchronization.
    """

    def __init__(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        raw_detection_row: Optional[np.ndarray],
        recognizer: FaceRecognitionService,
        gallery: GalleryManager,
        alert_service: AlertService,
        callback: Optional[Callable] = None,
        camera_id: Optional[int] = None,
        location_tag: str = "Main Camera",
    ) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self.frame = frame  # No copy needed: producer-consumer ensures sequential access
        self.bbox = bbox
        self.raw_detection_row = raw_detection_row.copy() if raw_detection_row is not None else None
        self.recognizer = recognizer
        self.gallery = gallery
        self.alert_service = alert_service
        self.callback = callback
        self.camera_id = camera_id
        self.location_tag = location_tag
        self.signals = RecognitionSignals()

    def run(self) -> None:
        """Execute embedding extraction and gallery lookup."""
        try:
            # Step 1+2: Extract embedding and demographics in a single pass.
            # This avoids the double-inference bug where InsightFace's full
            # pipeline (SCRFD + ArcFace + GenderAge) was run twice per face.
            embedding, demographics = self.recognizer.extract_embedding_and_demographics(
                self.frame, self.raw_detection_row
            )
            age = demographics.age if demographics else None
            gender = demographics.gender if demographics else None

            match: Optional[MatchResult] = None
            if embedding is not None:
                # Step 3: Query GalleryManager
                match = self.gallery.match_embedding(embedding)

                if match is not None:
                    # Step 4: Trigger AlertService (cooldown check, DB, sound, signal)
                    self.alert_service.process_match(
                        match=match,
                        frame=self.frame,
                        bbox=self.bbox,
                        camera_id=self.camera_id,
                        location_tag=self.location_tag,
                    )

            # Direct callback invocation for instant identity synchronization
            if self.callback is not None:
                try:
                    self.callback(match, self.bbox, age, gender)
                except Exception as cb_err:
                    logger.debug("Direct callback error: %s", cb_err)

            self.signals.match_completed.emit(match, self.bbox, age, gender)
        except Exception as e:
            logger.error("RecognitionWorker task failed: %s", e)
            if self.callback is not None:
                try:
                    self.callback(None, self.bbox, None, None)
                except Exception:
                    pass
            self.signals.match_completed.emit(None, self.bbox, None, None)
