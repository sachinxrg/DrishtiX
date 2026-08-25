"""
DrishtiX v4.0 — Camera Capture & Detection Worker (QThread).

High-performance video capture loop running on a dedicated background QThread.
Integrates YuNet face detection with KCF tracking for frame-skipping and
dispatches SFace recognition to a QThreadPool worker pool.
"""

import logging
import time
from typing import List, Optional, Union

import cv2
import numpy as np
from PySide6.QtCore import QMutex, QMutexLocker, QThread, QThreadPool

from drishtix.core.constants import DEFAULT_INFERENCE_INTERVAL, RECOGNITION_POOL_SIZE
from drishtix.core.enums import CameraStatus, TargetCategory
from drishtix.core.signals import signal_bus
from drishtix.services.alert_service import AlertService
from drishtix.services.face_detection import FaceDetection, FaceDetectionService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.services.face_tracker import FaceTrackingManager, TrackedFace
from drishtix.services.gallery_manager import GalleryManager, MatchResult
from drishtix.utils.image_utils import draw_tactical_bbox, mat_to_qpixmap
from drishtix.workers.recognition_worker import RecognitionWorker

logger = logging.getLogger(__name__)


class CaptureWorker(QThread):
    """
    Video capture and inference worker thread.
    """

    def __init__(
        self,
        camera_source: Union[int, str] = 0,
        inference_interval: int = DEFAULT_INFERENCE_INTERVAL,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.camera_source = camera_source
        self.inference_interval = max(1, inference_interval)
        self._running = False
        self._mutex = QMutex()

        # Services
        self.detector = FaceDetectionService()
        self.recognizer = FaceRecognitionService()
        self.gallery = GalleryManager.get_instance()
        self.tracker = FaceTrackingManager()
        self.alert_service = AlertService.get_instance()

        # Recognition Thread Pool
        self._recog_pool = QThreadPool()
        self._recog_pool.setMaxThreadCount(RECOGNITION_POOL_SIZE)

        # Performance metrics
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._last_fps_time: float = time.time()

    def set_camera_source(self, source: Union[int, str]) -> None:
        """Update camera device or stream URL."""
        with QMutexLocker(self._mutex):
            self.camera_source = source

    def set_inference_interval(self, interval: int) -> None:
        """Update inference frame interval (1 to 10)."""
        with QMutexLocker(self._mutex):
            self.inference_interval = max(1, interval)

    def stop(self) -> None:
        """Signal thread to stop capture loop."""
        with QMutexLocker(self._mutex):
            self._running = False

    def is_running(self) -> bool:
        """Check if worker is currently running."""
        with QMutexLocker(self._mutex):
            return self._running

    def _open_camera(self) -> Optional[cv2.VideoCapture]:
        """Open OpenCV video capture device."""
        source = self.camera_source
        logger.info("Opening camera source: %s", source)

        # On Windows, cv2.CAP_DSHOW provides fast, reliable webcam access
        if isinstance(source, int):
            cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            try:
                device_idx = int(source)
                cap = cv2.VideoCapture(device_idx, cv2.CAP_DSHOW)
            except ValueError:
                cap = cv2.VideoCapture(str(source))

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info("Camera successfully opened: %s", source)
            signal_bus.camera_status_changed.emit(True)
            return cap

        logger.warning("Failed to open camera: %s", source)
        signal_bus.camera_status_changed.emit(False)
        return None

    def run(self) -> None:
        """Main camera capture loop."""
        with QMutexLocker(self._mutex):
            self._running = True

        cap = self._open_camera()
        frame_counter = 0
        consecutive_failures = 0

        while True:
            with QMutexLocker(self._mutex):
                if not self._running:
                    break

            if cap is None or not cap.isOpened():
                time.sleep(1.0)
                cap = self._open_camera()
                continue

            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                consecutive_failures += 1
                if consecutive_failures > 15:
                    logger.warning("Camera stream interrupted. Attempting reconnect...")
                    signal_bus.camera_status_changed.emit(False)
                    cap.release()
                    cap = None
                    consecutive_failures = 0
                    time.sleep(2.0)
                else:
                    time.sleep(0.03)
                continue

            consecutive_failures = 0
            frame_counter += 1

            # Update FPS rolling average
            self._calculate_fps()

            # Process frame
            annotated_frame = frame.copy()
            active_detections_summary: List[dict] = []

            # Run YuNet Detection (sub-3ms inference)
            if self.detector.is_initialized():
                detections = self.detector.detect_faces(frame)
                active_tracks = self.tracker.update_with_detections(detections)

                # Dispatch SFace recognition tasks for each active detected face
                for det in detections:
                    worker = RecognitionWorker(
                        frame=frame,
                        bbox=det.bbox,
                        raw_detection_row=det.raw_row,
                        recognizer=self.recognizer,
                        gallery=self.gallery,
                        alert_service=self.alert_service,
                    )
                    worker.signals.match_completed.connect(self._on_match_result)
                    self._recog_pool.start(worker)
            else:
                active_tracks = []

            # Draw tactical HUD bounding boxes ONLY for active visible faces
            for track in self.tracker.get_all_active_tracks():
                draw_tactical_bbox(
                    frame=annotated_frame,
                    bbox=track.bbox,
                    name=track.name,
                    category=track.category,
                    confidence=track.confidence,
                )
                active_detections_summary.append({
                    "bbox": track.bbox,
                    "name": track.name,
                    "category": track.category,
                    "confidence": track.confidence,
                })

            # Convert to QPixmap and emit to UI
            pixmap = mat_to_qpixmap(annotated_frame)
            if not pixmap.isNull():
                signal_bus.frame_ready.emit(pixmap, active_detections_summary)

            # Throttle to ~30 FPS loop rate
            time.sleep(0.01)

        # Cleanup
        if cap is not None and cap.isOpened():
            cap.release()
            signal_bus.camera_status_changed.emit(False)

        self._recog_pool.waitForDone(1000)
        logger.info("CaptureWorker stopped cleanly.")

    def _on_match_result(self, match: Optional[MatchResult], bbox: tuple) -> None:
        """Slot called when RecognitionWorker finishes gallery lookup."""
        if match is not None:
            self.tracker.assign_identity(
                bbox=bbox,
                name=match.target.full_name,
                category=match.target.category,
                confidence=match.confidence,
            )

    def _calculate_fps(self) -> None:
        """Calculate and periodically emit rolling average FPS."""
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._last_fps_time

        if elapsed >= 0.5:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_fps_time = now
            signal_bus.fps_updated.emit(round(self._fps, 1))
