"""
DrishtiX v5.0 — 21st UI CircularProgress Widget.

Lightweight, modern ring / donut progress indicator with smooth
transition animations, rounded caps, and anti-aliased geometry.
"""

from typing import Optional

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QRectF,
    QVariantAnimation,
    Qt,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from drishtix.ui.motion import _is_motion_reduced
from drishtix.ui.theme_tokens import Color, Typography


class CircularProgress(QWidget):
    """
    Circular / Donut arc progress indicator with 21st UI smooth animations.
    """

    def __init__(
        self,
        value: float = 0.0,
        max_value: float = 100.0,
        size: int = 40,
        thickness: int = 4,
        color_hex: str = Color.ACCENT,
        show_text: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._value = max(0.0, min(value, max_value))
        self._max_value = max_value if max_value > 0 else 100.0
        self._thickness = thickness
        self._color = QColor(color_hex)
        self._track_color = QColor(Color.BORDER_SUBTLE)
        self._show_text = show_text
        self._anim: Optional[QVariantAnimation] = None

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_value(self, value: float, color_hex: Optional[str] = None, animated: bool = False) -> None:
        """Update progress value (0.0 to max_value) with optional smooth easing transition."""
        target_val = max(0.0, min(value, self._max_value))
        if color_hex:
            self._color = QColor(color_hex)

        if animated and not _is_motion_reduced() and abs(target_val - self._value) > 0.5:
            if self._anim and self._anim.state() == QAbstractAnimation.State.Running:
                self._anim.stop()

            self._anim = QVariantAnimation(self)
            self._anim.setDuration(400)
            self._anim.setStartValue(float(self._value))
            self._anim.setEndValue(float(target_val))
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _on_step(v: float):
                self._value = float(v)
                self.update()

            self._anim.valueChanged.connect(_on_step)
            self._anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        else:
            self._value = target_val
            self.update()

    def set_color(self, color_hex: str) -> None:
        """Update the arc color."""
        self._color = QColor(color_hex)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)
        pad = self._thickness / 2.0 + 1.0
        rect = QRectF(pad, pad, side - 2 * pad, side - 2 * pad)

        # 1. Background track ring
        track_pen = QPen(self._track_color, self._thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        # 2. Progress Arc
        if self._value > 0:
            arc_pen = QPen(self._color, self._thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)

            start_angle = 90 * 16
            span_angle = -int((self._value / self._max_value) * 360 * 16)
            painter.drawArc(rect, start_angle, span_angle)

        # 3. Optional Center text
        if self._show_text:
            painter.setPen(QPen(QColor(Color.TEXT_PRIMARY)))
            font = QFont("Inter", 8, QFont.Weight.Bold)
            painter.setFont(font)
            pct = int((self._value / self._max_value) * 100)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{pct}%")

        painter.end()
