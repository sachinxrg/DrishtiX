"""
DrishtiX v4.0 — Background Ingestion Worker.

Runs periodic FBI Most Wanted API synchronization on a dedicated QThread.
Executes an initial sync at startup, then repeats every hour (configurable).

Thread Safety:
    The IngestionWorker uses QThread + moveToThread() so that its QTimers
    fire on the worker thread's event loop, not the main UI thread. This
    ensures the blocking asyncio.run_until_complete() call never freezes
    the PySide6 GUI.

Pipeline:
  1. Fetch all FBI wanted persons (paginated).
  2. Filter out already-ingested targets (by FBI UID).
  3. Download facial images, run YuNet detection, extract ArcFace/SFace embeddings.
  4. Persist to SQLite and hot-reload GalleryManager.
"""

import asyncio
import logging
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from drishtix.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class _IngestionHandler(QObject):
    """
    Internal handler that performs the actual sync work.
    Lives on a dedicated QThread via moveToThread().
    """

    sync_completed = Signal(int)  # Emits count of newly ingested targets
    sync_started = Signal()

    def __init__(
        self,
        interval_minutes: int = 60,
        enabled: bool = True,
        max_items_per_sync: int = 100,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.interval_minutes = max(5, interval_minutes)
        self.enabled = enabled
        self.max_items_per_sync = max_items_per_sync
        self.ingestion_service = IngestionService()
        self._sync_in_progress = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sync_timer)

        # Initial sync timer (fires once after 8 seconds to let the UI fully load first)
        self._initial_timer = QTimer(self)
        self._initial_timer.setSingleShot(True)
        self._initial_timer.timeout.connect(self._on_initial_sync)

    def start_timers(self) -> None:
        """Start the periodic synchronization timer and schedule initial sync."""
        if self.enabled:
            # Schedule initial sync after 8 seconds
            self._initial_timer.start(8000)

            # Start recurring hourly timer
            interval_ms = self.interval_minutes * 60 * 1000
            self._timer.start(interval_ms)
            logger.info(
                "FBI Ingestion Worker ENABLED (initial sync in 8s, recurring every %d min, max %d items/sync)",
                self.interval_minutes, self.max_items_per_sync,
            )
        else:
            logger.info("FBI Ingestion Worker is DISABLED. No automatic syncing.")

    def stop_timers(self) -> None:
        """Stop all timers."""
        self._timer.stop()
        self._initial_timer.stop()
        logger.info("FBI Ingestion Worker stopped.")

    def trigger_sync_now(self) -> None:
        """Immediately trigger a sync (can be called from UI button)."""
        self._on_sync_timer()

    def _on_initial_sync(self) -> None:
        """Initial startup sync."""
        logger.info("Running initial FBI Most Wanted sync on startup...")
        self._run_sync()

    def _on_sync_timer(self) -> None:
        """Periodic timer-driven sync."""
        logger.info("Running scheduled hourly FBI Most Wanted sync...")
        self._run_sync()

    def _run_sync(self) -> None:
        """Execute the async ingestion pipeline."""
        if self._sync_in_progress:
            logger.info("Sync already in progress, skipping.")
            return

        self._sync_in_progress = True
        self.sync_started.emit()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            count = loop.run_until_complete(
                self.ingestion_service.ingest_fbi_wanted_async(max_items=self.max_items_per_sync)
            )
            loop.close()

            self.sync_completed.emit(count)
            logger.info("FBI sync cycle complete. %d new targets ingested.", count)
        except Exception as e:
            logger.error("FBI background ingestion sync failed: %s", e)
            self.sync_completed.emit(0)
        finally:
            self._sync_in_progress = False


class IngestionWorker(QObject):
    """
    Background worker managing periodic FBI API target synchronization.

    Uses a dedicated QThread so that blocking network I/O and CPU-bound
    face detection/embedding extraction do not freeze the main UI thread.

    Attributes:
        interval_minutes: Sync interval in minutes (default: 60 = 1 hour).
        enabled: Whether automatic sync is active.
        max_items_per_sync: Maximum new targets to ingest per sync cycle.
    """

    sync_completed = Signal(int)  # Proxied from _IngestionHandler
    sync_started = Signal()

    def __init__(
        self,
        interval_minutes: int = 60,
        enabled: bool = True,
        max_items_per_sync: int = 100,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._thread = QThread()
        self._thread.setObjectName("IngestionThread")

        self._handler = _IngestionHandler(
            interval_minutes=interval_minutes,
            enabled=enabled,
            max_items_per_sync=max_items_per_sync,
        )
        # Move handler to dedicated thread — its QTimers will fire there
        self._handler.moveToThread(self._thread)

        # Proxy signals from the handler back to the main thread
        self._handler.sync_completed.connect(self.sync_completed)
        self._handler.sync_started.connect(self.sync_started)

        # Start timers once the thread's event loop is running
        self._thread.started.connect(self._handler.start_timers)

    def start(self) -> None:
        """Start the dedicated ingestion thread."""
        if not self._thread.isRunning():
            self._thread.start()
            logger.info("IngestionWorker thread started.")

    def stop(self) -> None:
        """Stop the ingestion thread and clean up."""
        self._handler.stop_timers()
        self._thread.quit()
        self._thread.wait(3000)
        logger.info("IngestionWorker thread stopped.")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic sync at runtime."""
        self._handler.enabled = enabled
        if enabled:
            self.start()
        else:
            self._handler.stop_timers()

    def trigger_sync_now(self) -> None:
        """Immediately trigger a sync (can be called from UI button)."""
        self._handler.trigger_sync_now()

