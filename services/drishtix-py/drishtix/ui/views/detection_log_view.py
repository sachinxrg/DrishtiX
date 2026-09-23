"""
DrishtiX v5.0 — Detection Log View.

Filterable history table for all past facial recognition matches with CSV export,
ConfidenceBar visual progression, and incident report generation.
"""

import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.enums import TargetCategory
from drishtix.core.signals import signal_bus
from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.session import get_session
from drishtix.services.export_service import ExportService
from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.widgets.confidence_bar import ConfidenceBar
from drishtix.ui.widgets.empty_state import EmptyStateWidget
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.section_header import SectionHeader

logger = logging.getLogger(__name__)


class DetectionLogView(QWidget):
    """Historical detection log browser and incident report generator."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._wire_signals()
        self.load_logs()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # ─── Section Header ──────────────────────────────────────────
        header = SectionHeader(
            "DETECTION INCIDENT HISTORY",
            "Filter, review and export past recognition matches with biometric confidence metrics",
            icon="logs",
        )
        layout.addWidget(header)

        # ─── Filter Bar ──────────────────────────────────────────────
        filter_card = QFrame()
        apply_class(filter_card, "neu-inset")
        filter_bar = QHBoxLayout(filter_card)
        filter_bar.setContentsMargins(10, 8, 10, 8)
        filter_bar.setSpacing(10)

        # Target Name Search
        self.txt_target_search = QLineEdit()
        self.txt_target_search.setPlaceholderText("Filter by target name...")
        self.txt_target_search.setClearButtonEnabled(True)
        self.txt_target_search.setFixedWidth(240)
        self.txt_target_search.textChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.txt_target_search)

        # Category Filter
        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.addItem("All Categories", None)
        self.cmb_cat_filter.addItem("Criminals Only", TargetCategory.CRIMINAL.value)
        self.cmb_cat_filter.addItem("Missing Persons Only", TargetCategory.MISSING_PERSON.value)
        self.cmb_cat_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.cmb_cat_filter)

        filter_bar.addStretch()

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(render_svg_icon("refresh", size=14))
        btn_refresh.clicked.connect(self.load_logs)
        filter_bar.addWidget(btn_refresh)

        btn_export = QPushButton("Export CSV Report")
        apply_class(btn_export, "btn-primary")
        btn_export.setIcon(render_svg_icon("download", normal_color=Color.WHITE, size=14))
        btn_export.clicked.connect(self._export_csv)
        filter_bar.addWidget(btn_export)

        layout.addWidget(filter_card)

        # ─── Logs Table in GlassCard ─────────────────────────────────
        table_card = GlassCard(variant=CardVariant.GLASS)
        table_card.set_accessible_info("Detection History", "Historical facial recognition incident logs")
        self._table_container_layout = table_card.content_layout()
        self._table_container_layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(table_card, stretch=1)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Log ID",
            "Target Name",
            "Category",
            "Match Confidence",
            "Location",
            "Timestamp",
            "Case Reference",
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 160)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        self._table_container_layout.addWidget(self.table)

        # Empty State
        self.empty_state = EmptyStateWidget(
            icon="logs",
            message="No Detection Incidents Recorded\nEvents will appear here as perimeter recognition matches occur.",
            action_text="Refresh Logs",
            action_callback=self.load_logs,
        )
        self._table_container_layout.addWidget(self.empty_state)
        self.empty_state.hide()

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(lambda _: self.load_logs())

    def load_logs(self) -> None:
        """Fetch and populate recent detection events."""
        try:
            self._load_logs()
        except Exception:
            logger.exception("Failed to load detection logs")
            self.table.hide()
            self.empty_state.set_message(
                "Could not load detection history.\nCheck the database connection and retry."
            )
            self.empty_state.show()

    def _load_logs(self) -> None:
        target_name = self.txt_target_search.text().strip() or None
        category = self.cmb_cat_filter.currentData()

        with get_session() as session:
            logs = DetectionLogDAO.get_recent(
                session,
                limit=200,
                category=category,
                target_name=target_name,
            )

            if not logs:
                self.table.hide()
                self.empty_state.set_message(
                    "No Detection Incidents Recorded\n"
                    "Events will appear here as perimeter recognition matches occur."
                )
                self.empty_state.show()
                return

            self.empty_state.hide()
            self.table.show()
            self.table.setRowCount(len(logs))

            for row, log in enumerate(logs):
                # 0. Log ID
                item_id = QTableWidgetItem(f"#{log.log_id}")
                item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_id)

                # 1. Name
                name_str = log.target.full_name if log.target else "Unknown"
                item_name = QTableWidgetItem(name_str)
                item_name.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 1, item_name)

                # 2. Category Badge
                cat_str = log.target.category if log.target else "UNKNOWN"
                is_crim = (cat_str == "CRIMINAL")
                lbl_badge = QLabel(cat_str.replace("_", " "))
                lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                apply_class(lbl_badge, "badge-criminal" if is_crim else "badge-missing")
                self.table.setCellWidget(row, 2, lbl_badge)

                # 3. Confidence Visual Bar
                conf_val = float(log.confidence or 0.0)
                conf_bar = ConfidenceBar(confidence=conf_val)
                self.table.setCellWidget(row, 3, conf_bar)

                # 4. Location
                item_loc = QTableWidgetItem(log.location_tag or "Main Perimeter")
                item_loc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 4, item_loc)

                # 5. Timestamp (Full ISO format)
                ts_str = log.detection_timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.detection_timestamp else "N/A"
                item_ts = QTableWidgetItem(ts_str)
                item_ts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, item_ts)

                # 6. Case Reference
                case_str = log.target.case_number if log.target else "N/A"
                item_case = QTableWidgetItem(case_str or "N/A")
                item_case.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 6, item_case)

    def _on_filter_changed(self) -> None:
        self.load_logs()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Report",
            f"drishtix_detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            count = ExportService.export_detection_logs_to_csv(
                output_file_path=file_path,
                category=self.cmb_cat_filter.currentData(),
                target_name=self.txt_target_search.text().strip() or None,
            )
        except Exception as exc:
            logger.exception("CSV export failed")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not write the report to:\n{file_path}\n\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Export Complete",
            f"Successfully exported {count} detection records to:\n{file_path}",
        )
