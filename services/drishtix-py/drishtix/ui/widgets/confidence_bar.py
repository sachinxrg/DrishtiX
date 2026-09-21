"""
DrishtiX v5.0 — ConfidenceBar Widget.

Visual match confidence bar for table cells and incident logs.
Displays a mini horizontal rounded bar with color-coded fill and percentage label.
"""

from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from drishtix.ui.theme_tokens import Color


class ConfidenceBar(QWidget):
    """
    Mini horizontal confidence bar for table cells.

    Thresholds:
      - >= 70%: Emerald (Strong Match)
      - 50% - 69%: Amber (Moderate Match)
      - < 50%: Rose / Slate (Low Match)
    """

    def __init__(
        self,
        confidence: float = 0.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._confidence = max(0.0, min(1.0, confidence))
        self.setFixedHeight(24)
        self.setMinimumWidth(80)

    def set_confidence(self, confidence: float) -> None:
        """Update confidence value (0.0 to 1.0)."""
        self._confidence = max(0.0, min(1.0, confidence))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pct = self._confidence * 100.0

        # Bar dimensions
        bar_w = w - 48.0
        bar_h = 6.0
        bar_y = (h - bar_h) / 2.0
        track_rect = QRectF(4.0, bar_y, bar_w, bar_h)

        # 1. Track background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Color.BORDER_SUBTLE))
        painter.drawRoundedRect(track_rect, 3.0, 3.0)

        # 2. Fill bar
        if pct >= 70.0:
            fill_color = QColor(Color.SAFE)
        elif pct >= 50.0:
            fill_color = QColor(Color.WARNING)
        else:
            fill_color = QColor(Color.CRITICAL)

        fill_w = max(4.0, bar_w * self._confidence)
        fill_rect = QRectF(4.0, bar_y, fill_w, bar_h)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(fill_rect, 3.0, 3.0)

        # 3. Percentage Text
        painter.setPen(QPen(fill_color))
        font = QFont("JetBrains Mono", 8, QFont.Weight.Bold)
        painter.setFont(font)
        text_rect = QRectF(w - 42.0, 0, 40.0, h)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"{pct:.1f}%")

        painter.end()
