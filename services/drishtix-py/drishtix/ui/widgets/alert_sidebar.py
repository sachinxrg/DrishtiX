"""
DrishtiX v4.0 — AlertSidebar Widget.

Real-time scrollable tactical alert queue sidebar with automatic 50-card memory pruning,
live count badge, and frosted glass aesthetic.
"""

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.constants import ALERT_SIDEBAR_WIDTH, MAX_ALERT_QUEUE_SIZE
from drishtix.core.signals import signal_bus
from drishtix.ui.widgets.alert_card import AlertCard


class AlertSidebar(QFrame):
    """Frosted Glass Alert sidebar container holding live detection cards."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("AlertSidebar")
        self.setFixedWidth(ALERT_SIDEBAR_WIDTH)

        self._cards: List[AlertCard] = []

        self._init_ui()
        self._wire_signals()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # ─── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        lbl_title = QLabel("LIVE TACTICAL ALERTS")
        lbl_title.setStyleSheet(
            "font-weight: 800; font-size: 13px; color: #0F172A; letter-spacing: 0.6px;"
        )
        header.addWidget(lbl_title)

        # Active Counter Badge
        self.lbl_count_badge = QLabel("0")
        self.lbl_count_badge.setStyleSheet(
            "background-color: #F1F5F9; color: #64748B; border: 1px solid #CBD5E1; "
            "border-radius: 999px; padding: 1px 7px; font-weight: 700; font-size: 10.5px;"
        )
        header.addWidget(self.lbl_count_badge)

        header.addStretch()

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.setStyleSheet(
            "font-size: 11px; padding: 2px 10px; font-weight: 600; border-radius: 8px;"
        )
        self.btn_clear.clicked.connect(self.clear_alerts)
        header.addWidget(self.btn_clear)

        main_layout.addLayout(header)

        # ─── Scroll Area ─────────────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.card_container = QWidget()
        self.card_container.setStyleSheet("background-color: transparent;")
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Empty state container
        self.empty_card = QFrame()
        self.empty_card.setStyleSheet(
            "background: rgba(255, 255, 255, 0.6); border: 1px dashed #CBD5E1; "
            "border-radius: 16px; padding: 30px 16px;"
        )
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(6)

        icon_lbl = QLabel("🛡️")
        icon_lbl.setStyleSheet("font-size: 26px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_lbl)

        self.lbl_empty = QLabel("Perimeter Secure\nNo Active Target Detections")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500; line-height: 1.4;")
        empty_layout.addWidget(self.lbl_empty)

        self.card_layout.addWidget(self.empty_card)

        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(self.add_alert)
        signal_bus.alert_cleared.connect(self.clear_alerts)

    def _update_count_badge(self) -> None:
        count = len(self._cards)
        self.lbl_count_badge.setText(str(count))
        if count > 0:
            self.lbl_count_badge.setStyleSheet(
                "background-color: #FFF1F2; color: #F43F5E; border: 1px solid #FECDD3; "
                "border-radius: 999px; padding: 1px 7px; font-weight: 800; font-size: 10.5px;"
            )
        else:
            self.lbl_count_badge.setStyleSheet(
                "background-color: #F1F5F9; color: #64748B; border: 1px solid #CBD5E1; "
                "border-radius: 999px; padding: 1px 7px; font-weight: 700; font-size: 10.5px;"
            )

    def add_alert(self, alert_data: dict) -> None:
        """
        Prepend a new alert card to the top of the queue.
        Prunes oldest card if queue exceeds MAX_ALERT_QUEUE_SIZE.
        """
        if self.empty_card.isVisible():
            self.empty_card.hide()

        card = AlertCard(alert_data, self.card_container)
        self._cards.insert(0, card)
        self.card_layout.insertWidget(0, card)

        # Enforce memory cap (50 cards max)
        while len(self._cards) > MAX_ALERT_QUEUE_SIZE:
            oldest_card = self._cards.pop()
            self.card_layout.removeWidget(oldest_card)
            oldest_card.deleteLater()

        self._update_count_badge()

    def clear_alerts(self) -> None:
        """Remove all alert cards from the queue."""
        for card in self._cards:
            self.card_layout.removeWidget(card)
            card.deleteLater()

        self._cards.clear()
        self.empty_card.show()
        self._update_count_badge()
