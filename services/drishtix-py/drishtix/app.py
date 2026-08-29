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
    """
    Configure structured logging with structlog (F7).

    Wraps stdlib logging so all existing `logging.getLogger()` calls work
    unchanged. Adds:
    - Automatic correlation_id injection for request tracing
    - Timestamp formatting
    - Log level and logger name in structured output
    - JSON output when LOG_FORMAT=json, colored console output otherwise
    """
    import os
    import structlog

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose renderer based on environment
    use_json = os.environ.get("LOG_FORMAT", "").lower() == "json"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if use_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the dark tactical command QSS stylesheet."""
    qss_path = Path(__file__).parent / "ui" / "styles" / "drishtix_glass.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            stylesheet = f.read()
        app.setStyleSheet(stylesheet)
        logger.info("Loaded glassmorphism stylesheet: %s", qss_path.name)
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

    # 1. Initialize SQLite Database (with optional SQLCipher encryption)
    init_db(settings.database.path, encryption_key=settings.database.encryption_key)

    # 2. Run data retention enforcement (purge expired snapshots & logs)
    from drishtix.services.retention_service import RetentionService
    retention = RetentionService.get_instance()
    retention.run_full_purge()

    # 3. Populate In-Memory Gallery
    gallery = GalleryManager.get_instance()
    gallery.set_match_threshold(settings.recognition.match_threshold)
    loaded_count = gallery.reload_gallery()
    logger.info("Pre-loaded %d facial embeddings into tactical gallery", loaded_count)

    # 4. Create Qt Application
    # High-DPI scaling attributes for modern displays
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set default font
    font = QFont("Inter", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # Apply Dark Stylesheet
    load_stylesheet(app)

    # 5. Initialize Background Workers & Services
    from drishtix.services.telegram_service import TelegramService
    TelegramService.get_instance().update_config(
        bot_token=settings.alerts.telegram_bot_token,
        chat_id=settings.alerts.telegram_chat_id,
        enabled=settings.alerts.telegram_enabled,
    )

    capture_worker = CaptureWorker(
        camera_source=settings.camera.source,
        inference_interval=settings.detection.inference_interval,
    )

    ingestion_worker = IngestionWorker(
        interval_minutes=60,
        enabled=True,
        max_items_per_sync=100,
    )
    ingestion_worker.start()

    # 6. Create Main Command Window
    main_window = MainWindow(capture_worker=capture_worker)

    # 7. Start Video Capture Loop
    capture_worker.start()

    return app, main_window, capture_worker
