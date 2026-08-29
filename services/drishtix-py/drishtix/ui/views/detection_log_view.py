"""
DrishtiX v4.0 — Detection Log View.

Filterable history table for all past facial recognition matches with CSV export.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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


class DetectionLogView(QWidget):
    """Historical detection log browser and incident report generator."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._wire_signals()
        self.load_logs()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ─── Filter Bar ──────────────────────────────────────────────
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        # Target Name Search
        self.txt_target_search = QLineEdit()
        self.txt_target_search.setPlaceholderText("🔍 Filter by target name...")
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
        btn_refresh.clicked.connect(self.load_logs)
        filter_bar.addWidget(btn_refresh)

        btn_export = QPushButton("Export CSV Report")
        btn_export.setProperty("class", "btn-primary")
        btn_export.clicked.connect(self._export_csv)
        filter_bar.addWidget(btn_export)

        layout.addLayout(filter_bar)

        # ─── Logs Table ──────────────────────────────────────────────
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
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(lambda _: self.load_logs())

    def load_logs(self) -> None:
        """Fetch and populate recent detection events."""
        target_name = self.txt_target_search.text().strip() or None
        category = self.cmb_cat_filter.currentData()

        with get_session() as session:
            logs = DetectionLogDAO.get_recent(
                session,
                limit=200,
                category=category,
                target_name=target_name,
            )

            self.table.setRowCount(len(logs))

            for row, log in enumerate(logs):
                # Log ID
                item_id = QTableWidgetItem(f"#{log.log_id}")
                item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_id)

                # Name
                name_str = log.target.full_name if log.target else "Unknown"
                item_name = QTableWidgetItem(name_str)
                item_name.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 1, item_name)

                # Category Badge
                cat_str = log.target.category if log.target else "UNKNOWN"
                is_crim = (cat_str == "CRIMINAL")
                lbl_badge = QLabel(cat_str.replace("_", " "))
                lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_badge.setProperty("class", "badge-criminal" if is_crim else "badge-missing")
                self.table.setCellWidget(row, 2, lbl_badge)

                # Confidence
                item_conf = QTableWidgetItem(log.confidence_display)
                item_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_conf.setForeground(QColor("#10B981"))
                self.table.setItem(row, 3, item_conf)

                # Location
                item_loc = QTableWidgetItem(log.location_tag or "Main Perimeter")
                item_loc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 4, item_loc)

                # Timestamp
                ts_str = log.detection_timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.detection_timestamp else "N/A"
                item_ts = QTableWidgetItem(ts_str)
                item_ts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, item_ts)

                # Case Reference
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
        if file_path:
            category = self.cmb_cat_filter.currentData()
            count = ExportService.export_detection_logs_to_csv(
                output_file_path=file_path,
                category=category,
            )
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {count} detection records to:\n{file_path}",
            )
