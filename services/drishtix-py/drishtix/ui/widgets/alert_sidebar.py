"""
DrishtiX v4.0 — AlertSidebar Widget.

Real-time scrollable tactical alert queue sidebar with automatic 50-card memory pruning.
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
    """Alert sidebar container holding live detection cards."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("AlertSidebar")
        self.setFixedWidth(ALERT_SIDEBAR_WIDTH)

        self._cards: List[AlertCard] = []

        self._init_ui()
        self._wire_signals()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ─── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl_title = QLabel("LIVE TACTICAL ALERTS")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #E8EAED; letter-spacing: 0.5px;")
        header.addWidget(lbl_title)

        header.addStretch()

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.setStyleSheet("font-size: 11px; padding: 2px 8px;")
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
        self.card_layout.setSpacing(8)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Empty state label
        self.lbl_empty = QLabel("No active tactical alerts\nSurveillance perimeter secure")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #555A65; font-size: 12px; padding: 40px 0;")
        self.card_layout.addWidget(self.lbl_empty)

        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(self.add_alert)
        signal_bus.alert_cleared.connect(self.clear_alerts)

    def add_alert(self, alert_data: dict) -> None:
        """
        Prepend a new alert card to the top of the queue.
        Prunes oldest card if queue exceeds MAX_ALERT_QUEUE_SIZE.
        """
        # Hide empty state on first alert
        if self.lbl_empty.isVisible():
            self.lbl_empty.hide()

        card = AlertCard(alert_data, self.card_container)
        self._cards.insert(0, card)
        self.card_layout.insertWidget(0, card)

        # Enforce memory cap (50 cards max)
        while len(self._cards) > MAX_ALERT_QUEUE_SIZE:
            oldest_card = self._cards.pop()
            self.card_layout.removeWidget(oldest_card)
            oldest_card.deleteLater()

    def clear_alerts(self) -> None:
        """Remove all alert cards from the queue."""
        for card in self._cards:
            self.card_layout.removeWidget(card)
            card.deleteLater()

        self._cards.clear()
        self.lbl_empty.show()
