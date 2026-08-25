"""
DrishtiX v4.0 — AlertCard Widget.

Tactical notification card rendered in the live alert queue sidebar.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.constants import ALERT_CARD_THUMBNAIL_SIZE
from drishtix.core.enums import TargetCategory


class AlertCard(QFrame):
    """Bento-styled tactical alert card."""

    def __init__(self, data: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data = data

        category_str = data.get("category", "CRIMINAL").upper()
        is_criminal = (category_str == "CRIMINAL")

        if is_criminal:
            self.setProperty("class", "alert-card alert-card-criminal")
        else:
            self.setProperty("class", "alert-card alert-card-missing")

        self.setFixedHeight(84)
        self._init_ui(data, is_criminal)

    def _init_ui(self, data: dict, is_criminal: bool) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Snapshot Thumbnail
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(ALERT_CARD_THUMBNAIL_SIZE, ALERT_CARD_THUMBNAIL_SIZE)
        self.lbl_thumb.setStyleSheet("background-color: #0D0F14; border-radius: 4px; border: 1px solid #2E3140;")
        self.lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)

        snapshot_pixmap: Optional[QPixmap] = data.get("snapshot")
        if snapshot_pixmap and not snapshot_pixmap.isNull():
            scaled = snapshot_pixmap.scaled(
                ALERT_CARD_THUMBNAIL_SIZE,
                ALERT_CARD_THUMBNAIL_SIZE,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_thumb.setPixmap(scaled)
        else:
            self.lbl_thumb.setText("NO IMG")
            self.lbl_thumb.setStyleSheet("color: #555A65; font-size: 10px;")

        layout.addWidget(self.lbl_thumb)

        # 2. Metadata Column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Top Row: Name + Category Badge
        top_row = QHBoxLayout()
        name_color = "#FF4D2E" if is_criminal else "#00D4FF"
        lbl_name = QLabel(data.get("full_name", "Unknown Target"))
        lbl_name.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {name_color};")
        top_row.addWidget(lbl_name)

        badge_class = "badge-criminal" if is_criminal else "badge-missing"
        lbl_badge = QLabel(data.get("category", "CRIMINAL").replace("_", " "))
        lbl_badge.setProperty("class", badge_class)
        top_row.addWidget(lbl_badge)
        top_row.addStretch()

        info_layout.addLayout(top_row)

        # Middle Row: Case Number
        case_no = data.get("case_number", "N/A")
        lbl_case = QLabel(f"CASE: {case_no}")
        lbl_case.setStyleSheet("color: #9AA0A6; font-size: 11px;")
        info_layout.addWidget(lbl_case)

        # Bottom Row: Match Confidence + Time
        bot_row = QHBoxLayout()
        conf_val = data.get("confidence", 0.0)
        lbl_conf = QLabel(f"MATCH: {conf_val * 100:.1f}%")
        lbl_conf.setStyleSheet("color: #34D399; font-weight: 600; font-size: 11px;")
        bot_row.addWidget(lbl_conf)

        ts: datetime = data.get("timestamp", datetime.now())
        time_str = ts.strftime("%H:%M:%S")
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("color: #555A65; font-family: monospace; font-size: 11px;")
        bot_row.addWidget(lbl_time)
        bot_row.addStretch()

        info_layout.addLayout(bot_row)
        layout.addLayout(info_layout)
