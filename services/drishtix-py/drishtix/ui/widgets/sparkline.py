"""
DrishtiX v5.0 — Sparkline Widget.

Lightweight, pure QPainter-based micro trend chart for KPI cards and telemetry.
Draws a smooth cubic spline with a translucent gradient fill under the curve.
"""

from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from drishtix.ui.theme_tokens import Color


class Sparkline(QWidget):
    """
    Micro sparkline trend widget.

    Renders a smoothed spline from a series of integer/float points.
    Ideal for embedding inside KPICard to display 24-hour / multi-day trends.
    """

    def __init__(
        self,
        data: Optional[List[float]] = None,
        color_hex: str = Color.ACCENT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._data: List[float] = data if data else [0.0]
        self._color = QColor(color_hex)
        self.setFixedHeight(28)
        self.setMinimumWidth(60)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_data(self, data: List[float], color_hex: Optional[str] = None) -> None:
        """Update sparkline data points and optional line color."""
        self._data = data if data else [0.0]
        if color_hex:
            self._color = QColor(color_hex)
        self.update()

    def paintEvent(self, event) -> None:
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_top = 4.0
        pad_bot = 4.0
        draw_h = h - pad_top - pad_bot

        min_val = min(self._data)
        max_val = max(self._data)
        val_range = max_val - min_val if max_val > min_val else 1.0

        n = len(self._data)
        if n == 1:
            # Draw a flat horizontal line
            y = pad_top + draw_h / 2.0
            painter.setPen(QPen(self._color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(2, y), QPointF(w - 2, y))
            return

        # Compute point coordinates
        points: List[QPointF] = []
        dx = (w - 6.0) / (n - 1)
        for i, val in enumerate(self._data):
            x = 3.0 + i * dx
            # Invert y so max_val is near the top
            normalized = (val - min_val) / val_range
            y = pad_top + (1.0 - normalized) * draw_h
            points.append(QPointF(x, y))

        # Build smooth path using control points
        path = QPainterPath()
        path.moveTo(points[0])

        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            ctrl1 = QPointF(p0.x() + (p1.x() - p0.x()) / 2.0, p0.y())
            ctrl2 = QPointF(p0.x() + (p1.x() - p0.x()) / 2.0, p1.y())
            path.cubicTo(ctrl1, ctrl2, p1)

        # 1. Fill gradient area under curve
        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), h)
        fill_path.lineTo(points[0].x(), h)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0, pad_top, 0, h)
        c_top = QColor(self._color)
        c_top.setAlphaF(0.28)
        c_bot = QColor(self._color)
        c_bot.setAlphaF(0.0)
        gradient.setColorAt(0.0, c_top)
        gradient.setColorAt(1.0, c_bot)

        painter.fillPath(fill_path, gradient)

        # 2. Draw smooth stroke line
        pen = QPen(self._color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, pen)

        # 3. Draw endpoint marker dot
        last_pt = points[-1]
        painter.setBrush(self._color)
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(last_pt, 3.0, 3.0)

        painter.end()
