"""
DrishtiX v4.0 — Background Ingestion Worker.

Runs periodic API polling and external registry synchronization on a background timer.
Migrated from: com.drishtix.service.ingestion.BackgroundIngestionEngine (Java)
"""

import asyncio
import logging
from typing import Optional

from PySide6.QtCore import QObject, QTimer

from drishtix.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class IngestionWorker(QObject):
    """
    Background worker managing periodic target synchronization.
    """

    def __init__(
        self,
        interval_minutes: int = 60,
        enabled: bool = False,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.interval_minutes = max(5, interval_minutes)
        self.enabled = enabled
        self.ingestion_service = IngestionService()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sync_timer)

    def start(self) -> None:
        """Start the periodic synchronization timer."""
        if self.enabled:
            interval_ms = self.interval_minutes * 60 * 1000
            self._timer.start(interval_ms)
            logger.info("Ingestion worker started (sync interval: %d min)", self.interval_minutes)

    def stop(self) -> None:
        """Stop the timer."""
        self._timer.stop()
        logger.info("Ingestion worker stopped.")

    def trigger_sync_now(self) -> None:
        """Immediately trigger a background sync run."""
        self._on_sync_timer()

    def _on_sync_timer(self) -> None:
        """Periodic sync execution."""
        logger.info("Starting background target ingestion sync...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            count = loop.run_until_complete(self.ingestion_service.ingest_fbi_wanted_async(max_items=5))
            loop.close()
            logger.info("Background target sync complete. %d new targets added.", count)
        except Exception as e:
            logger.error("Background ingestion sync failed: %s", e)
