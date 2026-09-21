"""
DrishtiX v5.0 — Dashboard View.

Primary operational command center featuring BentoGrid architecture:
- Top KPI strip with inline sparklines and circular progress rings
- Live video feed with tactical HUD overlay
- Real-time scrollable frosted glass alert queue
- 24-hour activity density heatmap
- System compute health telemetry
"""

import logging
from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.signals import signal_bus
from drishtix.services.analytics_service import AnalyticsKPIs, DetectionAnalyticsService
from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.widgets.activity_heatmap import ActivityHeatmap
from drishtix.ui.widgets.alert_sidebar import AlertSidebar
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.kpi_card import KPICard
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus
from drishtix.ui.widgets.section_header import SectionHeader
from drishtix.ui.widgets.system_health_card import SystemHealthCard
from drishtix.ui.widgets.video_label import VideoLabel
from drishtix.workers.capture_worker import CaptureWorker

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Primary operational tactical surveillance dashboard."""

    def __init__(
        self,
        capture_worker: Optional[CaptureWorker] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.capture_worker = capture_worker

        self._init_ui()
        self._wire_signals()
        self.refresh_metrics()

        # Telemetry refresh timer
        self._kpi_timer = QTimer(self)
        self._kpi_timer.timeout.connect(self.refresh_metrics)
        self._kpi_timer.start(5000)

    def _init_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # ─── Row 1: Top Bento KPI Metric Cards (4 Tiles) ─────────────
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(Spacing.MD)

        self.kpi_total = KPICard("Total Detections", "0", icon="analytics", accent_color=Color.ACCENT)
        self.kpi_unique = KPICard("Unique Targets", "0", icon="target", accent_color=Color.SAFE)
        self.kpi_confidence = KPICard("Avg Confidence", "0.0%", icon="zap", accent_color=Color.WARNING)
        self.kpi_cameras = KPICard("Active Perimeter", "1 Node", icon="camera", accent_color=Color.INFO)

        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_unique)
        kpi_layout.addWidget(self.kpi_confidence)
        kpi_layout.addWidget(self.kpi_cameras)

        main_layout.addLayout(kpi_layout)

        # ─── Row 2: Video Stream (Left) + Alert Queue (Right) ────────
        center_layout = QHBoxLayout()
        center_layout.setSpacing(Spacing.LG)

        # Video Panel
        video_card = GlassCard(variant=CardVariant.GLASS)
        video_card.set_accessible_info("Video Feed Panel", "Live surveillance camera stream")
        video_layout = video_card.content_layout()
        video_layout.setContentsMargins(14, 14, 14, 14)
        video_layout.setSpacing(10)

        # Header controls with 21st UI camera icon
        header = SectionHeader("LIVE SURVEILLANCE PERIMETER", icon="camera")

        self.lbl_live_badge = PillBadge("● LIVE FEED", PillStatus.LIVE)
        header.add_action(self.lbl_live_badge)

        self.lbl_spec_pill = PillBadge("CAM 01 • 1280×720 • 30 FPS", PillStatus.NEUTRAL)
        header.add_action(self.lbl_spec_pill)

        self.btn_toggle_feed = QPushButton("Stop Feed")
        self.btn_toggle_feed.setFixedHeight(28)
        self.btn_toggle_feed.setIcon(render_svg_icon("video", size=14))
        self.btn_toggle_feed.clicked.connect(self._toggle_feed)
        header.add_action(self.btn_toggle_feed)

        video_layout.addWidget(header)

        # Video Surface
        self.video_label = VideoLabel()
        video_layout.addWidget(self.video_label, stretch=1)

        center_layout.addWidget(video_card, stretch=65)

        # Right: Alert Queue Sidebar
        self.alert_sidebar = AlertSidebar()
        center_layout.addWidget(self.alert_sidebar, stretch=35)

        main_layout.addLayout(center_layout, stretch=1)

        # ─── Row 3: 24h Activity Heatmap (Left) + Compute Health (Right) ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(Spacing.LG)

        # Heatmap Card
        heatmap_card = GlassCard(variant=CardVariant.GLASS)
        heatmap_layout = heatmap_card.content_layout()
        heatmap_layout.setContentsMargins(14, 12, 14, 12)
        heatmap_layout.setSpacing(8)

        lbl_heatmap_title = QLabel("24-HOUR SURVEILLANCE ACTIVITY DENSITY")
        apply_class(lbl_heatmap_title, "type-caption")
        lbl_heatmap_title.setStyleSheet(f"font-weight: 700; color: {Color.TEXT_MUTED}; letter-spacing: 0.5px;")
        heatmap_layout.addWidget(lbl_heatmap_title)

        self.activity_heatmap = ActivityHeatmap()
        heatmap_layout.addWidget(self.activity_heatmap)

        bottom_layout.addWidget(heatmap_card, stretch=65)

        # System Health Card
        self.health_card = SystemHealthCard()
        bottom_layout.addWidget(self.health_card, stretch=35)

        main_layout.addLayout(bottom_layout)

        scroll.setWidget(container)

        root_vbox = QVBoxLayout(self)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.addWidget(scroll)

    def _wire_signals(self) -> None:
        signal_bus.frame_ready.connect(self._on_frame_ready)
        signal_bus.camera_status_changed.connect(self._on_camera_status)
        signal_bus.alert_created.connect(lambda _: self.refresh_metrics())

    def refresh_metrics(self) -> None:
        """Fetch real-time aggregation metrics to update KPI cards and heatmap."""
        try:
            kpis: AnalyticsKPIs = DetectionAnalyticsService.get_kpis()
            self.kpi_total.set_value(f"{kpis.total_detections:,}", Color.ACCENT)
            self.kpi_unique.set_value(f"{kpis.unique_targets:,}", Color.SAFE)
            self.kpi_confidence.set_value(f"{kpis.avg_confidence * 100:.1f}%", Color.WARNING)
            self.kpi_cameras.set_value(f"{kpis.active_cameras} Node{'s' if kpis.active_cameras != 1 else ''}", Color.TEXT_PRIMARY)

            # Circular progress for confidence
            self.kpi_confidence.set_progress_ring(kpis.avg_confidence * 100.0, 100.0, Color.WARNING)

            # Hourly trend sparkline for total detections
            hourly_data = DetectionAnalyticsService.get_hourly_distribution()
            sparkline_values = [float(item["count"]) for item in hourly_data]
            self.kpi_total.set_sparkline_data(sparkline_values, Color.ACCENT)

            # Activity heatmap update
            self.activity_heatmap.set_data(hourly_data)
        except Exception:
            logger.exception("Dashboard metrics refresh failed")

    def _on_frame_ready(self, pixmap: QPixmap, detections: list) -> None:
        """Slot for incoming annotated camera frame."""
        self.video_label.set_frame(pixmap)

    def _on_camera_status(self, connected: bool) -> None:
        if connected:
            self.lbl_live_badge.set_text("● LIVE FEED")
            self.lbl_live_badge.set_status(PillStatus.LIVE)
            self.btn_toggle_feed.setText("Stop Feed")
        else:
            self.lbl_live_badge.set_text("● OFFLINE")
            self.lbl_live_badge.set_status(PillStatus.OFFLINE)
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
