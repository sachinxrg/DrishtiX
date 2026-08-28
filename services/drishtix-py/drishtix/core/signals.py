"""
DrishtiX v4.0 — Centralized Qt Signal Bus.

Singleton QObject that provides typed signals for cross-component communication.
Replaces Java's Platform.runLater() callbacks with Qt's thread-safe signal/slot
mechanism. All worker threads emit signals on this bus; UI widgets connect slots.

Usage:
    from drishtix.core.signals import signal_bus

    # In a worker thread:
    signal_bus.match_found.emit({"target_id": 1, "confidence": 0.92, ...})

    # In a UI widget:
    signal_bus.match_found.connect(self._on_match_found)
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap


class SignalBus(QObject):
    """
    Centralized signal bus for thread-safe cross-component communication.

    All signals are defined as class-level Signal instances. Worker threads
    emit signals; UI widgets connect slots. Qt guarantees that slots connected
    with the default (AutoConnection) type are executed on the receiver's
    thread, making this safe for UI updates from background threads.
    """

    # ─── Video Pipeline ─────────────────────────────────────────────
    frame_ready = Signal(QPixmap, list)
    """Emitted by CaptureWorker with the annotated frame and detection list."""

    camera_status_changed = Signal(bool)
    """Emitted when camera connects (True) or disconnects (False)."""

    fps_updated = Signal(float)
    """Emitted periodically with the rolling-average FPS value."""

    # ─── Recognition Pipeline ───────────────────────────────────────
    match_found = Signal(dict)
    """
    Emitted by RecognitionWorker when a face matches a gallery target.
    Payload dict: {
        'target_id': int,
        'full_name': str,
        'category': str,
        'case_number': str,
        'confidence': float,
        'snapshot': QPixmap,
        'bbox': tuple[int, int, int, int],
        'timestamp': datetime
    }
    """

    recognition_error = Signal(str)
    """Emitted when the recognition pipeline encounters an error."""

    # ─── Alert System ───────────────────────────────────────────────
    alert_created = Signal(dict)
    """Emitted by AlertService when a new alert card should be rendered."""

    alert_cleared = Signal()
    """Emitted when the user clicks 'Clear All' on the alert sidebar."""

    # ─── Data Change Notifications ──────────────────────────────────
    targets_changed = Signal()
    """Emitted after any CRUD operation on the target_registry table."""

    gallery_reloaded = Signal(int)
    """Emitted after the in-memory gallery is reloaded. Payload: active target count."""

    # ─── System Health ──────────────────────────────────────────────
    db_status_changed = Signal(bool)
    """Emitted when database connectivity changes. True=healthy, False=offline."""

    config_changed = Signal(str, object)
    """Emitted when a config value is changed at runtime. (key, new_value)."""

    memory_updated = Signal(float)
    """Emitted periodically with current RSS memory usage in MB."""


# Module-level singleton instance
signal_bus = SignalBus()
