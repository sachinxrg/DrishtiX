"""
DrishtiX v4.0 — Application Bootstrap and Lifecycle Manager.

Initializes configuration, database schema, in-memory face embedding gallery,
PySide6 QApplication, dark tactical QSS stylesheets, and background worker threads.
"""

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from drishtix.core.config import get_settings
from drishtix.core.constants import APP_NAME, APP_VERSION
from drishtix.dao.session import initialize as init_db, shutdown as shutdown_db
from drishtix.services.gallery_manager import GalleryManager
from drishtix.services.face_detection import FaceDetectionService
from drishtix.services.face_recognition import FaceRecognitionService
from drishtix.ui.main_window import MainWindow
from drishtix.workers.capture_worker import CaptureWorker
from drishtix.workers.ingestion_worker import IngestionWorker

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the dark tactical command QSS stylesheet."""
    qss_path = Path(__file__).parent / "ui" / "styles" / "drishtix_dark.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            stylesheet = f.read()
        app.setStyleSheet(stylesheet)
        logger.info("Loaded tactical dark stylesheet: %s", qss_path.name)
    else:
        logger.warning("Stylesheet not found at %s", qss_path)


def create_app() -> tuple[QApplication, MainWindow, CaptureWorker]:
    """
    Bootstrap the complete DrishtiX application environment.

    Returns:
        Tuple of (QApplication, MainWindow, CaptureWorker).
    """
    settings = get_settings()
    setup_logging(settings.app.log_level)

    logger.info("Initializing %s v%s...", APP_NAME, APP_VERSION)

    # 1. Initialize SQLite Database
    init_db(settings.database.path)

    # 2. Populate In-Memory Gallery
    gallery = GalleryManager.get_instance()
    gallery.set_match_threshold(settings.recognition.match_threshold)
    loaded_count = gallery.reload_gallery()
    logger.info("Pre-loaded %d facial embeddings into tactical gallery", loaded_count)

    # 3. Create Qt Application
    # High-DPI scaling attributes for modern displays
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Apply Dark Stylesheet
    load_stylesheet(app)

    # 4. Initialize Background Workers
    capture_worker = CaptureWorker(
        camera_source=settings.camera.source,
        inference_interval=settings.detection.inference_interval,
    )

    ingestion_worker = IngestionWorker(enabled=False)
    ingestion_worker.start()

    # 5. Create Main Command Window
    main_window = MainWindow(capture_worker=capture_worker)

    # 6. Start Video Capture Loop
    capture_worker.start()

    return app, main_window, capture_worker
