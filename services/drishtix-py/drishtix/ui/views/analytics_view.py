"""
DrishtiX v5.0 — Analytics Dashboard View.

Comprehensive visual analytics featuring Bento KPI metric cards with sparklines,
24h hourly timeline bar chart, category breakdown donut chart, multi-day trend line chart,
and top detected targets table.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.signals import signal_bus
from drishtix.services.analytics_service import AnalyticsKPIs, DetectionAnalyticsService
from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.widgets.chart_widget import (
    TacticalBarChart,
    TacticalLineChart,
    TacticalPieChart,
)
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.kpi_card import KPICard
from drishtix.ui.widgets.section_header import SectionHeader

logger = logging.getLogger(__name__)


class AnalyticsView(QWidget):
    """Analytics and Intelligence Command Dashboard."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._wire_signals()
        self.refresh_dashboard()

    def _init_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.LG)

        # ─── Header ──────────────────────────────────────────────────
        header = SectionHeader(
            "TACTICAL INTELLIGENCE ANALYTICS",
            "Comprehensive pattern analysis and identity telemetry",
            icon="analytics",
        )

        btn_refresh = QPushButton("Refresh Analytics")
        btn_refresh.setIcon(render_svg_icon("refresh", size=14))
        btn_refresh.clicked.connect(self.refresh_dashboard)
        header.add_action(btn_refresh)

        layout.addWidget(header)

        # ─── Row 1: KPI Bento Cards (4 Tiles) ────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(Spacing.MD)

        self.kpi_total = KPICard("Total Detections", "0", icon="analytics", accent_color=Color.ACCENT)
        self.kpi_unique = KPICard("Unique Targets", "0", icon="target", accent_color=Color.SAFE)
        self.kpi_confidence = KPICard("Avg Confidence", "0.0%", icon="zap", accent_color=Color.WARNING)
        self.kpi_cameras = KPICard("Active Perimeter", "1 Node", icon="camera", accent_color=Color.INFO)

        kpi_row.addWidget(self.kpi_total)
        kpi_row.addWidget(self.kpi_unique)
        kpi_row.addWidget(self.kpi_confidence)
        kpi_row.addWidget(self.kpi_cameras)

        layout.addLayout(kpi_row)

        # ─── Row 2: Charts (Hourly Bar + Category Donut) ─────────────
        charts_row_1 = QHBoxLayout()
        charts_row_1.setSpacing(Spacing.MD)

        self.bar_chart = TacticalBarChart()
        charts_row_1.addWidget(self.bar_chart, stretch=3)

        self.pie_chart = TacticalPieChart()
        charts_row_1.addWidget(self.pie_chart, stretch=2)

        layout.addLayout(charts_row_1)

        # ─── Row 3: Trend Line + Top Targets Table ────────────────────
        charts_row_2 = QHBoxLayout()
        charts_row_2.setSpacing(Spacing.MD)

        self.line_chart = TacticalLineChart()
        charts_row_2.addWidget(self.line_chart, stretch=3)

        # Top Targets Card Container
        top_targets_card = GlassCard(variant=CardVariant.GLASS)
        top_targets_card.set_accessible_info("Top Targets", "Most frequently detected targets")
        top_targets_layout = top_targets_card.content_layout()
        top_targets_layout.setContentsMargins(14, 12, 14, 12)
        top_targets_layout.setSpacing(10)

        lbl_top_title = QLabel("TOP IDENTIFIED TARGETS")
        apply_class(lbl_top_title, "type-caption")
        lbl_top_title.setStyleSheet(f"font-weight: 700; color: {Color.TEXT_MUTED}; letter-spacing: 0.5px;")
        top_targets_layout.addWidget(lbl_top_title)

        self.top_table = QTableWidget()
        self.top_table.setColumnCount(3)
        self.top_table.setHorizontalHeaderLabels(["Target Name", "Category", "Hits"])
        self.top_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.top_table.verticalHeader().setVisible(False)
        self.top_table.setAlternatingRowColors(True)
        top_targets_layout.addWidget(self.top_table)

        charts_row_2.addWidget(top_targets_card, stretch=2)

        layout.addLayout(charts_row_2)

        scroll.setWidget(container)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(lambda _: self.refresh_dashboard())

    def refresh_dashboard(self) -> None:
        """Query aggregation metrics and update all widgets/charts."""
        try:
            self._refresh_dashboard()
        except Exception:
            logger.exception("Analytics refresh failed")

    def _refresh_dashboard(self) -> None:
        # 1. Update KPIs
        kpis: AnalyticsKPIs = DetectionAnalyticsService.get_kpis()
        self.kpi_total.set_value(f"{kpis.total_detections:,}", Color.ACCENT)
        self.kpi_unique.set_value(f"{kpis.unique_targets:,}", Color.SAFE)
        self.kpi_confidence.set_value(f"{kpis.avg_confidence * 100:.1f}%", Color.WARNING)
        self.kpi_cameras.set_value(f"{kpis.active_cameras} Node{'s' if kpis.active_cameras != 1 else ''}", Color.TEXT_PRIMARY)

        # Circular progress ring for confidence
        self.kpi_confidence.set_progress_ring(kpis.avg_confidence * 100.0, 100.0, Color.WARNING)

        # Hourly data for bar chart and sparkline
        hourly_data = DetectionAnalyticsService.get_hourly_distribution()
        sparkline_values = [float(item["count"]) for item in hourly_data]
        self.kpi_total.set_sparkline_data(sparkline_values, Color.ACCENT)
        self.bar_chart.update_data(hourly_data)

        # Category and daily trends
        category_data = DetectionAnalyticsService.get_category_breakdown()
        self.pie_chart.update_data(category_data)

        daily_data = DetectionAnalyticsService.get_daily_trend(days=7)
        self.line_chart.update_data(daily_data)

        # 3. Update Top Targets Table
        top_targets = DetectionAnalyticsService.get_top_targets(limit=5)
        self.top_table.setRowCount(len(top_targets))

        for row, item in enumerate(top_targets):
            # Name
            name_item = QTableWidgetItem(str(item.get("full_name", "N/A")))
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.top_table.setItem(row, 0, name_item)

            # Category
            cat_str = str(item.get("category", "N/A"))
            is_crim = (cat_str == "CRIMINAL")
            lbl_cat = QLabel(cat_str.replace("_", " "))
            lbl_cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            apply_class(lbl_cat, "badge-criminal" if is_crim else "badge-missing")
            self.top_table.setCellWidget(row, 1, lbl_cat)

            # Hits
            hits_item = QTableWidgetItem(str(item.get("count", 0)))
            hits_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            hits_item.setForeground(QColor(Color.ACCENT))
            self.top_table.setItem(row, 2, hits_item)
