"""
DrishtiX v4.0 — AlertSidebar Widget.

Real-time scrollable tactical alert queue sidebar with automatic 50-card memory pruning,
live count badge, and frosted glass aesthetic.
Refactored: PillBadge, EmptyStateWidget, apply_class(), zero inline setStyleSheet.
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
from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.widgets.alert_card import AlertCard
from drishtix.ui.widgets.empty_state import EmptyStateWidget
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus


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
        apply_class(lbl_title, "view-title")
        header.addWidget(lbl_title)

        # Active Counter Badge
        self.lbl_count_badge = PillBadge("0", PillStatus.NEUTRAL)
        header.addWidget(self.lbl_count_badge)

        header.addStretch()

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setIcon(render_svg_icon("x", size=12))
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.clicked.connect(self.clear_alerts)
        header.addWidget(self.btn_clear)

        main_layout.addLayout(header)

        # ─── Scroll Area ─────────────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Reusable Empty state component
        self.empty_card = EmptyStateWidget(
            icon="shield",
            message="Perimeter Secure\nNo Active Target Detections",
        )
        self.card_layout.addWidget(self.empty_card)

        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area)

    def _wire_signals(self) -> None:
        signal_bus.alert_created.connect(self.add_alert)
        signal_bus.alert_cleared.connect(self.clear_alerts)

    def _update_count_badge(self) -> None:
        count = len(self._cards)
        self.lbl_count_badge.set_text(str(count))
        if count > 0:
            self.lbl_count_badge.set_status(PillStatus.CRITICAL)
        else:
            self.lbl_count_badge.set_status(PillStatus.NEUTRAL)

    def add_alert(self, alert_data: dict) -> None:
        """
        Prepend a new alert card to the top of the queue.
        Prunes oldest card if queue exceeds MAX_ALERT_QUEUE_SIZE.
        """
        # Key off the card list, not isVisible(): the sidebar may not have been
        # shown yet, in which case isVisible() is False and the empty state
        # would be left sitting above the real alert cards.
        if not self._cards:
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
