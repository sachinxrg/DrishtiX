"""
DrishtiX v4.0 — Analytics Dashboard View.

Comprehensive visual analytics featuring Bento KPI metric cards, 24h hourly timeline bar chart,
category breakdown donut chart, multi-day trend line chart, and top detected targets table.
Migrated from: com.drishtix.controller.AnalyticsController (Java)
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
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
from drishtix.ui.widgets.chart_widget import (
    TacticalBarChart,
    TacticalLineChart,
    TacticalPieChart,
)


class KPICard(QFrame):
    """Bento-styled metric KPI card."""

    def __init__(self, title: str, initial_value: str = "--", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "kpi-card")
        self.setFixedHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setProperty("class", "kpi-title")
        layout.addWidget(self.lbl_title)

        self.lbl_val = QLabel(initial_value)
        self.lbl_val.setProperty("class", "kpi-val")
        layout.addWidget(self.lbl_val)

    def set_value(self, value: str, color_hex: Optional[str] = None) -> None:
        self.lbl_val.setText(value)
        if color_hex:
            self.lbl_val.setStyleSheet(f"color: {color_hex}; font-size: 24px; font-weight: 700;")


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
        scroll.setStyleSheet("background-color: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ─── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl_title = QLabel("TACTICAL INTELLIGENCE ANALYTICS")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #0F172A; letter-spacing: 0.5px;")
        header.addWidget(lbl_title)

        header.addStretch()

        btn_refresh = QPushButton("Refresh Analytics")
        btn_refresh.clicked.connect(self.refresh_dashboard)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # ─── Row 1: KPI Bento Cards ──────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_total = KPICard("Total Detections", "0")
        kpi_row.addWidget(self.kpi_total)

        self.kpi_unique = KPICard("Unique Targets", "0")
        kpi_row.addWidget(self.kpi_unique)

        self.kpi_confidence = KPICard("Avg Match Confidence", "0.0%")
        kpi_row.addWidget(self.kpi_confidence)

        self.kpi_cameras = KPICard("Active Perimeter Nodes", "1")
        kpi_row.addWidget(self.kpi_cameras)

        layout.addLayout(kpi_row)

        # ─── Row 2: Charts (Hourly Bar + Category Donut) ─────────────
        charts_row_1 = QHBoxLayout()
        charts_row_1.setSpacing(12)

        self.bar_chart = TacticalBarChart()
        charts_row_1.addWidget(self.bar_chart, stretch=3)

        self.pie_chart = TacticalPieChart()
        charts_row_1.addWidget(self.pie_chart, stretch=2)

        layout.addLayout(charts_row_1)

        # ─── Row 3: Trend Line + Top Targets Table ────────────────────
        charts_row_2 = QHBoxLayout()
        charts_row_2.setSpacing(12)

        self.line_chart = TacticalLineChart()
        charts_row_2.addWidget(self.line_chart, stretch=3)

        # Top Targets Card Container
        top_targets_card = QFrame()
        top_targets_card.setProperty("class", "bento-card")
        top_targets_layout = QVBoxLayout(top_targets_card)
        top_targets_layout.setContentsMargins(12, 12, 12, 12)
        top_targets_layout.setSpacing(8)

        lbl_top_title = QLabel("TOP IDENTIFIED TARGETS")
        lbl_top_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #0F172A;")
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

        # Container inside Scroll Area
        scroll.setWidget(container)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(lambda _: self.refresh_dashboard())

    def refresh_dashboard(self) -> None:
        """Query aggregation metrics and update all widgets/charts."""
        # 1. Update KPIs
        kpis: AnalyticsKPIs = DetectionAnalyticsService.get_kpis()
        self.kpi_total.set_value(f"{kpis.total_detections:,}", "#4F6BFB")
        self.kpi_unique.set_value(f"{kpis.unique_targets:,}", "#10B981")
        self.kpi_confidence.set_value(f"{kpis.avg_confidence * 100:.1f}%", "#F59E0B")
        self.kpi_cameras.set_value(str(kpis.active_cameras), "#0F172A")

        # 2. Update Charts
        hourly_data = DetectionAnalyticsService.get_hourly_distribution()
        self.bar_chart.update_data(hourly_data)

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
            self.top_table.setItem(row, 0, name_item)

            # Category
            cat_str = str(item.get("category", "N/A"))
            is_crim = (cat_str == "CRIMINAL")
            lbl_cat = QLabel(cat_str.replace("_", " "))
            lbl_cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_cat.setProperty("class", "badge-criminal" if is_crim else "badge-missing")
            self.top_table.setCellWidget(row, 1, lbl_cat)

            # Hits
            hits_item = QTableWidgetItem(str(item.get("count", 0)))
            hits_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            hits_item.setForeground(QColor("#4F6BFB"))
            self.top_table.setItem(row, 2, hits_item)
