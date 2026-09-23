"""
DrishtiX v5.0 — Tactical AlertCard Component.

Next-level Light Glassmorphism with softened frosted crimson glass (Criminal)
and vivid electric cyan-blue frosted glass (Missing Persons).
"""

from datetime import datetime
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

from drishtix.core.constants import ALERT_CARD_THUMBNAIL_SIZE
from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus


class AlertCard(QFrame):
    """
    Frosted Glassmorphic Tactical Alert Card.
    - Criminal: Translucent soft crimson glass with left crimson accent.
    - Missing Person: Translucent cyan glass with left cyan accent.
    """

    def __init__(self, data: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data = data

        category_str = data.get("category", "CRIMINAL").upper()
        is_criminal = "CRIM" in category_str

        if is_criminal:
            apply_class(self, "alert-card alert-card-criminal")
        else:
            apply_class(self, "alert-card alert-card-missing")

        self.setFixedHeight(84)
        self._init_ui(data, is_criminal)

    def _init_ui(self, data: dict, is_criminal: bool) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(10)

        # ─── 1. Biometric Snapshot Thumbnail Container ──────────────
        thumb_container = QFrame()
        thumb_container.setFixedSize(ALERT_CARD_THUMBNAIL_SIZE + 4, ALERT_CARD_THUMBNAIL_SIZE + 4)
        thumb_class = "alert-thumb-criminal" if is_criminal else "alert-thumb-missing"
        apply_class(thumb_container, thumb_class)

        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(ALERT_CARD_THUMBNAIL_SIZE, ALERT_CARD_THUMBNAIL_SIZE)
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
            avatar_pix = render_svg_pixmap("user", Color.TEXT_MUTED, size=24)
            if not avatar_pix.isNull():
                self.lbl_thumb.setPixmap(avatar_pix)
            else:
                self.lbl_thumb.setText("NO IMG")
            apply_class(self.lbl_thumb, "empty-state-message")

        thumb_layout.addWidget(self.lbl_thumb)
        layout.addWidget(thumb_container)

        # ─── 2. Tactical Metadata Column ────────────────────────────
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Top Row: Target Name + Category Pill Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        lbl_name = QLabel(data.get("full_name", "Unknown Target"))
        apply_class(lbl_name, "type-h3")
        top_row.addWidget(lbl_name)

        badge_class = "badge-criminal" if is_criminal else "badge-missing"
        category_label = "CRIMINAL" if is_criminal else "MISSING"
        lbl_badge = QLabel(category_label)
        apply_class(lbl_badge, badge_class)
        top_row.addWidget(lbl_badge)
        top_row.addStretch()

        info_layout.addLayout(top_row)

        # Middle Row: Case Reference
        case_no = data.get("case_number", "N/A")
        lbl_case = QLabel(f"REF: {case_no}")
        apply_class(lbl_case, "type-caption")
        info_layout.addWidget(lbl_case)

        # Bottom Row: Match Confidence Chip + Demographic Chip + Timestamp
        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)

        # Match Chip
        conf_val = data.get("confidence", 0.0)
        match_status = PillStatus.CRITICAL if is_criminal else PillStatus.INFO
        lbl_conf = PillBadge(f"MATCH {conf_val * 100:.1f}%", match_status)
        bot_row.addWidget(lbl_conf)

        # Demographic Chip
        age_val = data.get("age")
        gender_val = data.get("gender")
        if age_val or gender_val:
            gender_key = str(gender_val).upper() if gender_val else ""
            if gender_key == "M":
                gender_sym = "♂"
            elif gender_key == "F":
                gender_sym = "♀"
            else:
                gender_sym = str(gender_val or "")
            demo_text = f"{gender_sym} ~{age_val}y" if age_val else gender_sym
            demo_status = PillStatus.CRITICAL if is_criminal else PillStatus.INFO
            lbl_demo = PillBadge(demo_text.strip(), demo_status)
            bot_row.addWidget(lbl_demo)

        bot_row.addStretch()

        # Timestamp
        ts: datetime = data.get("timestamp", datetime.now())
        time_str = ts.strftime("%H:%M:%S")
        lbl_time = QLabel(time_str)
        apply_class(lbl_time, "status-metric")
        bot_row.addWidget(lbl_time)

        info_layout.addLayout(bot_row)
        layout.addLayout(info_layout)
