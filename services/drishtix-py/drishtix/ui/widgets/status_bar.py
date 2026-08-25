"""
DrishtiX v4.0 — Tactical Command Status Bar.

Real-time bottom bar showing system diagnostics, rolling FPS, camera health,
database connectivity, active target count, and memory RSS usage.
"""

import os
from typing import Optional

import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from drishtix.core.constants import STATUS_BAR_HEIGHT, STATUS_UPDATE_INTERVAL_MS
from drishtix.core.signals import signal_bus
from drishtix.dao.session import test_connection
from drishtix.services.gallery_manager import GalleryManager


class StatusBar(QFrame):
    """Bottom telemetry and diagnostics bar."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(STATUS_BAR_HEIGHT)

        self._process = psutil.Process(os.getpid())

        self._init_ui()
        self._wire_signals()

        # Telemetry update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_diagnostics)
        self._timer.start(STATUS_UPDATE_INTERVAL_MS)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(24)

        # 1. System Status
        self.lbl_system = QLabel("● SYSTEM READY")
        self.lbl_system.setStyleSheet("color: #34D399; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.lbl_system)

        # 2. Camera Status
        self.lbl_camera = QLabel("CAM: DISCONNECTED")
        self.lbl_camera.setStyleSheet("color: #FF4D2E; font-size: 11px; font-weight: 500;")
        layout.addWidget(self.lbl_camera)

        # 3. FPS Metric
        self.lbl_fps = QLabel("FPS: 0.0")
        self.lbl_fps.setStyleSheet("color: #9AA0A6; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.lbl_fps)

        # 4. Database Status
        self.lbl_db = QLabel("DB: CONNECTED")
        self.lbl_db.setStyleSheet("color: #34D399; font-size: 11px;")
        layout.addWidget(self.lbl_db)

        # 5. Active Target Count
        self.lbl_targets = QLabel("TARGETS: 0")
        self.lbl_targets.setStyleSheet("color: #4A9EFF; font-size: 11px; font-weight: 500;")
        layout.addWidget(self.lbl_targets)

        layout.addStretch()

        # 6. Memory RSS Usage
        self.lbl_memory = QLabel("RAM: 0 MB")
        self.lbl_memory.setStyleSheet("color: #9AA0A6; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.lbl_memory)

        # 7. Version
        lbl_version = QLabel("v4.0.0-tactical")
        lbl_version.setStyleSheet("color: #555A65; font-size: 10px;")
        layout.addWidget(lbl_version)

    def _wire_signals(self) -> None:
        """Connect to global signal bus."""
        signal_bus.fps_updated.connect(self._on_fps_updated)
        signal_bus.camera_status_changed.connect(self._on_camera_status)
        signal_bus.db_status_changed.connect(self._on_db_status)
        signal_bus.gallery_reloaded.connect(self._on_gallery_reloaded)

    def _on_fps_updated(self, fps: float) -> None:
        color = "#34D399" if fps >= 15.0 else ("#FBBF24" if fps >= 8.0 else "#FF4D2E")
        self.lbl_fps.setText(f"FPS: {fps:.1f}")
        self.lbl_fps.setStyleSheet(f"color: {color}; font-family: monospace; font-weight: bold; font-size: 11px;")

    def _on_camera_status(self, connected: bool) -> None:
        if connected:
            self.lbl_camera.setText("CAM: ONLINE")
            self.lbl_camera.setStyleSheet("color: #34D399; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_camera.setText("CAM: OFFLINE")
            self.lbl_camera.setStyleSheet("color: #FF4D2E; font-weight: bold; font-size: 11px;")

    def _on_db_status(self, connected: bool) -> None:
        if connected:
            self.lbl_db.setText("DB: ONLINE")
            self.lbl_db.setStyleSheet("color: #34D399; font-size: 11px;")
        else:
            self.lbl_db.setText("DB: OFFLINE")
            self.lbl_db.setStyleSheet("color: #FF4D2E; font-size: 11px;")

    def _on_gallery_reloaded(self, count: int) -> None:
        self.lbl_targets.setText(f"TARGETS: {count}")

    def _update_diagnostics(self) -> None:
        """Periodic memory and health check."""
        try:
            mem_info = self._process.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024)
            self.lbl_memory.setText(f"RAM: {rss_mb:.0f} MB")
            signal_bus.memory_updated.emit(rss_mb)

            # Update target count from gallery
            tgt_count = GalleryManager.get_instance().get_target_count()
            self.lbl_targets.setText(f"TARGETS: {tgt_count}")
        except Exception:
            pass
