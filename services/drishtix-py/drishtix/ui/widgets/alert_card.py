"""
DrishtiX v4.0 — Tactical AlertCard Component.

Next-level Light Glassmorphism + Blurred Red Frosted Glass (Criminal)
and Vivid Electric Cyan-Blue Frosted Glass (Missing Persons).
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


class AlertCard(QFrame):
    """
    Next-Level Frosted Glassmorphic Tactical Alert Card.
    - Criminal: Translucent blurred crimson-red card with glowing red border.
    - Missing Person: Translucent vivid electric cyan-blue card with glowing cyan border.
    """

    def __init__(self, data: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data = data

        category_str = data.get("category", "CRIMINAL").upper()
        is_criminal = "CRIM" in category_str

        if is_criminal:
            self.setProperty("class", "alert-card alert-card-criminal")
        else:
            self.setProperty("class", "alert-card alert-card-missing")

        self.setFixedHeight(92)
        self._init_ui(data, is_criminal)

    def _init_ui(self, data: dict, is_criminal: bool) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 12, 10)
        layout.setSpacing(12)

        # ─── 1. Biometric Snapshot Thumbnail Container ──────────────
        thumb_container = QFrame()
        thumb_container.setFixedSize(68, 68)
        
        if is_criminal:
            thumb_container.setStyleSheet(
                "background-color: #FEE2E2; border-radius: 12px; border: 2px solid rgba(239, 68, 68, 0.55);"
            )
        else:
            thumb_container.setStyleSheet(
                "background-color: #E0F2FE; border-radius: 12px; border: 2px solid rgba(6, 182, 212, 0.55);"
            )

        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(64, 64)
        self.lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumb.setStyleSheet("border-radius: 10px; background: transparent;")

        snapshot_pixmap: Optional[QPixmap] = data.get("snapshot")
        if snapshot_pixmap and not snapshot_pixmap.isNull():
            scaled = snapshot_pixmap.scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_thumb.setPixmap(scaled)
        else:
            self.lbl_thumb.setText("NO IMG")
            no_img_bg = "#FECDD3" if is_criminal else "#BAE6FD"
            no_img_fg = "#991B1B" if is_criminal else "#0369A1"
            self.lbl_thumb.setStyleSheet(
                f"color: {no_img_fg}; font-size: 10px; font-weight: bold; background: {no_img_bg}; border-radius: 10px;"
            )

        thumb_layout.addWidget(self.lbl_thumb)
        layout.addWidget(thumb_container)

        # ─── 2. Tactical Metadata Column ────────────────────────────
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        info_layout.setContentsMargins(0, 2, 0, 2)

        # Top Row: Target Name + Category Pill Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        name_color = "#991B1B" if is_criminal else "#0C4A6E"
        lbl_name = QLabel(data.get("full_name", "Unknown Target"))
        lbl_name.setStyleSheet(
            f"font-weight: 800; font-size: 14px; color: {name_color}; letter-spacing: 0.2px;"
        )
        top_row.addWidget(lbl_name)

        badge_class = "badge-criminal" if is_criminal else "badge-missing"
        category_label = "⚠️ CRIMINAL" if is_criminal else "🔍 MISSING"
        lbl_badge = QLabel(category_label)
        lbl_badge.setProperty("class", badge_class)
        top_row.addWidget(lbl_badge)
        top_row.addStretch()

        info_layout.addLayout(top_row)

        # Middle Row: Case Reference
        case_no = data.get("case_number", "N/A")
        case_color = "#7F1D1D" if is_criminal else "#0369A1"
        lbl_case = QLabel(f"REF: {case_no}")
        lbl_case.setStyleSheet(
            f"color: {case_color}; font-size: 11px; font-family: monospace; font-weight: 700;"
        )
        info_layout.addWidget(lbl_case)

        # Bottom Row: Match Confidence Chip + Demographic Chip + Timestamp
        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)

        # Match Chip (High contrast pill)
        conf_val = data.get("confidence", 0.0)
        if is_criminal:
            match_style = (
                "background-color: #FFFFFF; color: #DC2626; border: 1.5px solid #F87171; "
                "border-radius: 6px; padding: 2px 7px; font-weight: 800; font-size: 11px;"
            )
        else:
            match_style = (
                "background-color: #FFFFFF; color: #0284C7; border: 1.5px solid #38BDF8; "
                "border-radius: 6px; padding: 2px 7px; font-weight: 800; font-size: 11px;"
            )

        lbl_conf = QLabel(f"MATCH {conf_val * 100:.1f}%")
        lbl_conf.setStyleSheet(match_style)
        bot_row.addWidget(lbl_conf)

        # Demographic Chip (Age / Gender)
        age_val = data.get("age")
        gender_val = data.get("gender")
        if age_val or gender_val:
            gender_sym = "♂" if str(gender_val).upper() == "M" else ("♀" if str(gender_val).upper() == "F" else str(gender_val or ""))
            demo_text = f"{gender_sym} ~{age_val}y" if age_val else gender_sym
            demo_bg = "#FEE2E2" if is_criminal else "#E0F2FE"
            demo_fg = "#991B1B" if is_criminal else "#0369A1"
            demo_border = "#FCA5A5" if is_criminal else "#7DD3FC"
            lbl_demo = QLabel(demo_text.strip())
            lbl_demo.setStyleSheet(
                f"background-color: {demo_bg}; color: {demo_fg}; border: 1px solid {demo_border}; "
                "border-radius: 6px; padding: 2px 6px; font-weight: 700; font-size: 10.5px;"
            )
            bot_row.addWidget(lbl_demo)

        bot_row.addStretch()

        # Timestamp (Right-Aligned)
        ts: datetime = data.get("timestamp", datetime.now())
        time_str = ts.strftime("%H:%M:%S")
        ts_color = "#991B1B" if is_criminal else "#075985"
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet(
            f"color: {ts_color}; font-family: monospace; font-size: 11.5px; font-weight: 700;"
        )
        bot_row.addWidget(lbl_time)

        info_layout.addLayout(bot_row)
        layout.addLayout(info_layout)
