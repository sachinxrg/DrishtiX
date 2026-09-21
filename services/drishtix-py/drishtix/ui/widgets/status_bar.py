"""
DrishtiX v5.0 — 21st UI Tactical Command Status Bar.

Real-time bottom bar showing system diagnostics, rolling FPS, camera health,
database connectivity, active target count, CPU load, and memory RSS usage
enclosed in sleek frosted telemetry capsules with 21st.dev live breathing pulse.
"""

import os
import time
from typing import Optional

import psutil
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from drishtix.core.constants import APP_VERSION, STATUS_BAR_HEIGHT, STATUS_UPDATE_INTERVAL_MS
from drishtix.core.signals import signal_bus
from drishtix.dao.session import test_connection
from drishtix.services.gallery_manager import GalleryManager
from drishtix.ui.motion import PulsingStatusDot
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color
from drishtix.ui.widgets.pill_badge import StatusCapsule


class StatusBar(QFrame):
    """Bottom frosted telemetry and diagnostics bar with 21st UI live radar pulse."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(STATUS_BAR_HEIGHT)

        self._start_time = time.time()
        self._process = psutil.Process(os.getpid())
        self._db_check_every = max(1, int(5000 / STATUS_UPDATE_INTERVAL_MS))
        self._tick = 0

        self._init_ui()
        self._wire_signals()

        # Reflect real DB health immediately
        self._on_db_status(test_connection())

        # Telemetry update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_diagnostics)
        self._timer.start(STATUS_UPDATE_INTERVAL_MS)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        # 21st.dev Live Radar Breathing Dot
        self.pulse_dot = PulsingStatusDot(color_hex=Color.SAFE, dot_radius=3.5, max_aura_radius=8.5, parent=self)
        layout.addWidget(self.pulse_dot)

        # 1. System Status Capsule
        self.lbl_system = StatusCapsule("SYSTEM READY", status="safe")
        layout.addWidget(self.lbl_system)

        # 2. Camera Status Capsule
        self.lbl_camera = StatusCapsule("CAM: DISCONNECTED", status="critical")
        layout.addWidget(self.lbl_camera)

        # 3. FPS Metric Capsule
        self.lbl_fps = StatusCapsule("FPS: 0.0", status="neutral", monospace=True)
        layout.addWidget(self.lbl_fps)

        # 4. Database Status Capsule
        self.lbl_db = StatusCapsule("DB: CHECKING", status="neutral")
        layout.addWidget(self.lbl_db)

        # 5. Active Target Count Capsule
        self.lbl_targets = StatusCapsule("TARGETS: 0", status="accent")
        layout.addWidget(self.lbl_targets)

        layout.addStretch()

        # 6. CPU Usage Capsule
        self.lbl_cpu = StatusCapsule("CPU: 0%", status="neutral", monospace=True)
        layout.addWidget(self.lbl_cpu)

        # 7. Memory RSS Usage Capsule
        self.lbl_memory = StatusCapsule("RAM: 0 MB", status="neutral", monospace=True)
        layout.addWidget(self.lbl_memory)

        # 8. Version Pill
        lbl_version = QLabel(f"v{APP_VERSION}")
        apply_class(lbl_version, "type-micro")
        lbl_version.setStyleSheet("color: #64748B; font-weight: 700; padding: 2px 6px;")
        layout.addWidget(lbl_version)

    def _wire_signals(self) -> None:
        """Connect to global signal bus."""
        signal_bus.fps_updated.connect(self._on_fps_updated)
        signal_bus.camera_status_changed.connect(self._on_camera_status)
        signal_bus.db_status_changed.connect(self._on_db_status)
        signal_bus.gallery_reloaded.connect(self._on_gallery_reloaded)

    def _on_fps_updated(self, fps: float) -> None:
        if fps >= 15.0:
            status = "safe"
        elif fps >= 8.0:
            status = "warning"
        else:
            status = "critical"

        self.lbl_fps.set_text(f"FPS: {fps:.1f}")
        self.lbl_fps.set_capsule_status(status)

    def _on_camera_status(self, connected: bool) -> None:
        if connected:
            self.lbl_camera.set_text("CAM: ONLINE")
            self.lbl_camera.set_capsule_status("safe")
            self.pulse_dot.set_color(Color.SAFE)
        else:
            self.lbl_camera.set_text("CAM: OFFLINE")
            self.lbl_camera.set_capsule_status("critical")
            self.pulse_dot.set_color(Color.CRITICAL)

    def _on_db_status(self, connected: bool) -> None:
        if connected:
            self.lbl_db.set_text("DB: ONLINE")
            self.lbl_db.set_capsule_status("safe")
        else:
            self.lbl_db.set_text("DB: OFFLINE")
            self.lbl_db.set_capsule_status("critical")

    def _on_gallery_reloaded(self, count: int) -> None:
        self.lbl_targets.set_text(f"TARGETS: {count}")

    def _update_diagnostics(self) -> None:
        """Periodic memory, CPU, and health check."""
        self._tick += 1
        try:
            mem_info = self._process.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024)
            self.lbl_memory.set_text(f"RAM: {rss_mb:.0f} MB")
            signal_bus.memory_updated.emit(rss_mb)

            # CPU percentage
            cpu_pct = psutil.cpu_percent(interval=None)
            self.lbl_cpu.set_text(f"CPU: {cpu_pct:.0f}%")

            # Update target count from gallery
            tgt_count = GalleryManager.get_instance().get_target_count()
            self.lbl_targets.set_text(f"TARGETS: {tgt_count}")
        except Exception:
            pass

        # Poll database health
        if self._tick % self._db_check_every == 0:
            try:
                connected = test_connection()
            except Exception:
                connected = False
            self._on_db_status(connected)
            signal_bus.db_status_changed.emit(connected)
