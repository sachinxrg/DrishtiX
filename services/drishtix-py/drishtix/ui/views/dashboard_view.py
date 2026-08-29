"""
DrishtiX v4.0 — Dashboard View.

Primary operational command center featuring live video feed with tactical bounding box overlays,
HUD status telemetry, and real-time scrollable frosted glass alert queue.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.signals import signal_bus
from drishtix.ui.widgets.alert_sidebar import AlertSidebar
from drishtix.ui.widgets.video_label import VideoLabel
from drishtix.workers.capture_worker import CaptureWorker


class DashboardView(QWidget):
    """Main live surveillance command center view."""

    def __init__(
        self,
        capture_worker: Optional[CaptureWorker] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.capture_worker = capture_worker

        self._init_ui()
        self._wire_signals()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        # ─── Left: Video Feed Panel (Flex 3) ────────────────────────
        video_panel = QFrame()
        video_panel.setProperty("class", "bento-card")
        video_layout = QVBoxLayout(video_panel)
        video_layout.setContentsMargins(16, 16, 16, 16)
        video_layout.setSpacing(12)

        # Feed Controls Header
        header = QHBoxLayout()
        header.setSpacing(10)

        # Title
        lbl_feed_title = QLabel("LIVE SURVEILLANCE PERIMETER")
        lbl_feed_title.setStyleSheet(
            "font-weight: 800; font-size: 13px; color: #0F172A; letter-spacing: 0.6px;"
        )
        header.addWidget(lbl_feed_title)

        # Live Pulse Badge
        self.lbl_live_badge = QLabel("● LIVE FEED")
        self.lbl_live_badge.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
            "border-radius: 999px; padding: 2px 10px; font-weight: 800; font-size: 11px;"
        )
        header.addWidget(self.lbl_live_badge)

        # Camera Spec Pill
        self.lbl_spec_pill = QLabel("CAM 01 • 1280×720 • 30 FPS")
        self.lbl_spec_pill.setStyleSheet(
            "background-color: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 2px 8px; font-size: 10.5px; font-family: monospace; font-weight: 600;"
        )
        header.addWidget(self.lbl_spec_pill)

        header.addStretch()

        # Feed Control Button
        self.btn_toggle_feed = QPushButton("Stop Feed")
        self.btn_toggle_feed.setFixedHeight(30)
        self.btn_toggle_feed.setStyleSheet(
            "font-size: 11.5px; padding: 2px 14px; font-weight: 600; border-radius: 8px;"
        )
        self.btn_toggle_feed.clicked.connect(self._toggle_feed)
        header.addWidget(self.btn_toggle_feed)

        video_layout.addLayout(header)

        # Video Rendering Surface with Bezel
        self.video_label = VideoLabel()
        video_layout.addWidget(self.video_label, stretch=1)

        main_layout.addWidget(video_panel, stretch=3)

        # ─── Right: Alert Queue Sidebar (Fixed 380px) ───────────────
        self.alert_sidebar = AlertSidebar()
        main_layout.addWidget(self.alert_sidebar, stretch=0)

    def _wire_signals(self) -> None:
        signal_bus.frame_ready.connect(self._on_frame_ready)
        signal_bus.camera_status_changed.connect(self._on_camera_status)

    def _on_frame_ready(self, pixmap: QPixmap, detections: list) -> None:
        """Slot for incoming annotated camera frame."""
        self.video_label.set_frame(pixmap)

    def _on_camera_status(self, connected: bool) -> None:
        if connected:
            self.lbl_live_badge.setText("● LIVE FEED")
            self.lbl_live_badge.setStyleSheet(
                "background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; "
                "border-radius: 999px; padding: 2px 10px; font-weight: 800; font-size: 11px;"
            )
            self.btn_toggle_feed.setText("Stop Feed")
        else:
            self.lbl_live_badge.setText("● OFFLINE")
            self.lbl_live_badge.setStyleSheet(
                "background-color: #FFF1F2; color: #F43F5E; border: 1px solid #FECDD3; "
                "border-radius: 999px; padding: 2px 10px; font-weight: 800; font-size: 11px;"
            )
            self.btn_toggle_feed.setText("Start Feed")
            self.video_label.clear_frame()

    def _toggle_feed(self) -> None:
        if self.capture_worker is None:
            return

        if self.capture_worker.is_running():
            self.capture_worker.stop()
            self._on_camera_status(False)
        else:
            self.capture_worker.start()
            self._on_camera_status(True)
