"""
DrishtiX v4.0 — Tactical Command Status Bar.

Real-time bottom bar showing system diagnostics, rolling FPS, camera health,
database connectivity, active target count, and memory RSS usage
enclosed in sleek frosted telemetry capsules.
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
    """Bottom frosted telemetry and diagnostics bar."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(STATUS_BAR_HEIGHT + 4)  # 36px height

        self._process = psutil.Process(os.getpid())

        self._init_ui()
        self._wire_signals()

        # Telemetry update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_diagnostics)
        self._timer.start(STATUS_UPDATE_INTERVAL_MS)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # 1. System Status Capsule
        self.lbl_system = QLabel("● SYSTEM READY")
        self.lbl_system.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
            "border-radius: 6px; padding: 2px 8px; font-weight: 800; font-size: 10.5px;"
        )
        layout.addWidget(self.lbl_system)

        # 2. Camera Status Capsule
        self.lbl_camera = QLabel("CAM: DISCONNECTED")
        self.lbl_camera.setStyleSheet(
            "background-color: #FFF1F2; color: #F43F5E; border: 1px solid #FECDD3; "
            "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
        )
        layout.addWidget(self.lbl_camera)

        # 3. FPS Metric Capsule
        self.lbl_fps = QLabel("FPS: 0.0")
        self.lbl_fps.setStyleSheet(
            "background-color: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 2px 8px; font-family: monospace; font-size: 10.5px; font-weight: 700;"
        )
        layout.addWidget(self.lbl_fps)

        # 4. Database Status Capsule
        self.lbl_db = QLabel("DB: CONNECTED")
        self.lbl_db.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
            "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
        )
        layout.addWidget(self.lbl_db)

        # 5. Active Target Count Capsule
        self.lbl_targets = QLabel("TARGETS: 0")
        self.lbl_targets.setStyleSheet(
            "background-color: #EEF2FF; color: #4F6BFB; border: 1px solid #C7D2FE; "
            "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
        )
        layout.addWidget(self.lbl_targets)

        layout.addStretch()

        # 6. Memory RSS Usage Capsule
        self.lbl_memory = QLabel("RAM: 0 MB")
        self.lbl_memory.setStyleSheet(
            "background-color: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 2px 8px; font-family: monospace; font-size: 10.5px; font-weight: 700;"
        )
        layout.addWidget(self.lbl_memory)

        # 7. Version Pill
        lbl_version = QLabel("v4.0.0-tactical")
        lbl_version.setStyleSheet("color: #94A3B8; font-size: 10.5px; font-weight: 600; padding: 2px 4px;")
        layout.addWidget(lbl_version)

    def _wire_signals(self) -> None:
        """Connect to global signal bus."""
        signal_bus.fps_updated.connect(self._on_fps_updated)
        signal_bus.camera_status_changed.connect(self._on_camera_status)
        signal_bus.db_status_changed.connect(self._on_db_status)
        signal_bus.gallery_reloaded.connect(self._on_gallery_reloaded)

    def _on_fps_updated(self, fps: float) -> None:
        if fps >= 15.0:
            bg, fg, border = "#ECFDF5", "#059669", "#A7F3D0"
        elif fps >= 8.0:
            bg, fg, border = "#FFFBEB", "#D97706", "#FDE68A"
        else:
            bg, fg, border = "#FFF1F2", "#F43F5E", "#FECDD3"

        self.lbl_fps.setText(f"FPS: {fps:.1f}")
        self.lbl_fps.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {border}; "
            "border-radius: 6px; padding: 2px 8px; font-family: monospace; font-weight: 800; font-size: 10.5px;"
        )

    def _on_camera_status(self, connected: bool) -> None:
        if connected:
            self.lbl_camera.setText("CAM: ONLINE")
            self.lbl_camera.setStyleSheet(
                "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
                "border-radius: 6px; padding: 2px 8px; font-weight: 800; font-size: 10.5px;"
            )
        else:
            self.lbl_camera.setText("CAM: OFFLINE")
            self.lbl_camera.setStyleSheet(
                "background-color: #FFF1F2; color: #F43F5E; border: 1px solid #FECDD3; "
                "border-radius: 6px; padding: 2px 8px; font-weight: 800; font-size: 10.5px;"
            )

    def _on_db_status(self, connected: bool) -> None:
        if connected:
            self.lbl_db.setText("DB: ONLINE")
            self.lbl_db.setStyleSheet(
                "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
                "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
            )
        else:
            self.lbl_db.setText("DB: OFFLINE")
            self.lbl_db.setStyleSheet(
                "background-color: #FFF1F2; color: #F43F5E; border: 1px solid #FECDD3; "
                "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-weight: 700;"
            )

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
