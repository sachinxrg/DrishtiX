"""
DrishtiX v5.0 — ActivityHeatmap Widget.

24-hour horizontal activity heatmap strip showing detection density by hour.
Draws cells with variable intensity from subtle tint to deep vibrant indigo.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from drishtix.ui.theme_tokens import Color


class ActivityHeatmap(QWidget):
    """
    24-hour activity density strip.

    Displays 24 blocks (00:00 to 23:00) with color mapping based on detection counts.
    Supports hover tooltips for exact hour metrics.
    """

    def __init__(
        self,
        hourly_data: Optional[List[Dict[str, int]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumHeight(48)
        self.setFixedHeight(54)
        self.setMouseTracking(True)

        self._counts = [0] * 24
        if hourly_data:
            self.set_data(hourly_data)

    def set_data(self, hourly_data: List[Dict[str, int]]) -> None:
        """Update 24-hour data counts from list of {'hour': h, 'count': c}."""
        self._counts = [0] * 24
        for item in hourly_data:
            h = item.get("hour", 0)
            c = item.get("count", 0)
            if 0 <= h < 24:
                self._counts[h] = c
        self.update()

    def _get_cell_rect(self, index: int) -> QRectF:
        w = self.width()
        cell_w = (w - 24 * 3.0) / 24.0
        x = index * (cell_w + 3.0)
        return QRectF(x, 4.0, cell_w, 24.0)

    def mouseMoveEvent(self, event) -> None:
        pos = event.pos()
        for i in range(24):
            rect = self._get_cell_rect(i)
            if rect.contains(pos):
                cnt = self._counts[i]
                hour_str = f"{i:02d}:00 - {i:02d}:59"
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"⏰ {hour_str}\n📊 {cnt} Detection{'s' if cnt != 1 else ''}",
                    self,
                )
                return
        QToolTip.hideText()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        max_c = max(self._counts) if any(self._counts) else 1

        font_label = QFont("Inter", 8, QFont.Weight.Medium)
        painter.setFont(font_label)

        for i in range(24):
            rect = self._get_cell_rect(i)
            cnt = self._counts[i]

            # Color calculation
            if cnt == 0:
                cell_color = QColor(Color.CANVAS_ALT)
                border_color = QColor(Color.BORDER_SUBTLE)
            else:
                ratio = min(1.0, max(0.2, cnt / max_c))
                cell_color = QColor(Color.ACCENT)
                cell_color.setAlphaF(0.20 + ratio * 0.75)
                border_color = QColor(Color.ACCENT_BORDER)

            # Draw rounded block
            painter.setPen(QPen(border_color, 1.0))
            painter.setBrush(cell_color)
            painter.drawRoundedRect(rect, 4.0, 4.0)

            # Hour label markers below for selected milestones (0, 6, 12, 18, 23)
            if i in (0, 6, 12, 18, 23):
                painter.setPen(QPen(QColor(Color.TEXT_MUTED)))
                label_rect = QRectF(rect.x() - 6, 32.0, rect.width() + 12, 16.0)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"{i:02d}h")

        painter.end()
