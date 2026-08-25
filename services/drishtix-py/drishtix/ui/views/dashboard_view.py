"""
DrishtiX v4.0 — Dashboard View.

Primary operational screen featuring live video feed with tactical bounding box overlays
and real-time scrollable alert queue sidebar.
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
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ─── Left: Video Feed Panel (Flex 3) ────────────────────────
        video_panel = QFrame()
        video_panel.setProperty("class", "bento-card")
        video_layout = QVBoxLayout(video_panel)
        video_layout.setContentsMargins(12, 12, 12, 12)
        video_layout.setSpacing(8)

        # Feed Controls Header
        header = QHBoxLayout()
        lbl_feed_title = QLabel("LIVE SURVEILLANCE PERIMETER")
        lbl_feed_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #E8EAED; letter-spacing: 0.5px;")
        header.addWidget(lbl_feed_title)

        self.lbl_live_badge = QLabel("● LIVE")
        self.lbl_live_badge.setStyleSheet("color: #34D399; font-weight: bold; font-size: 11px; margin-left: 8px;")
        header.addWidget(self.lbl_live_badge)

        header.addStretch()

        self.btn_toggle_feed = QPushButton("Stop Feed")
        self.btn_toggle_feed.setFixedHeight(28)
        self.btn_toggle_feed.setStyleSheet("font-size: 11px; padding: 2px 12px;")
        self.btn_toggle_feed.clicked.connect(self._toggle_feed)
        header.addWidget(self.btn_toggle_feed)

        video_layout.addLayout(header)

        # Video Rendering Surface
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
            self.lbl_live_badge.setText("● LIVE")
            self.lbl_live_badge.setStyleSheet("color: #34D399; font-weight: bold; font-size: 11px; margin-left: 8px;")
            self.btn_toggle_feed.setText("Stop Feed")
        else:
            self.lbl_live_badge.setText("● OFFLINE")
            self.lbl_live_badge.setStyleSheet("color: #FF4D2E; font-weight: bold; font-size: 11px; margin-left: 8px;")
            self.btn_toggle_feed.setText("Start Feed")
            self.video_label.clear_frame()

    def _toggle_feed(self) -> None:
        """Toggle camera capture on/off."""
        if self.capture_worker is None:
            return

        if self.capture_worker.is_running():
            self.capture_worker.stop()
            self.capture_worker.wait(1000)
            self._on_camera_status(False)
        else:
            self.capture_worker.start()
            self._on_camera_status(True)
