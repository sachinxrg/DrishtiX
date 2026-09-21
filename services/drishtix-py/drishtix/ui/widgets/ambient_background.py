"""
DrishtiX v5.0 — AmbientBackground Widget.

Subtle multi-stop gradient mesh canvas that sits behind the content stack,
giving the app a soft, living-room-light feel instead of a flat white slab.
"""

from typing import Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from drishtix.ui.theme_tokens import Color


class AmbientBackground(QWidget):
    """
    Gradient mesh background widget.

    Paints a subtle multi-stop gradient from the CANVAS and MESH tokens,
    providing visual warmth without competing with foreground content.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Base Linear Gradient: top-left warm -> bottom-right cool
        base_grad = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        base_grad.setColorAt(0.0, QColor(Color.CANVAS))
        base_grad.setColorAt(0.4, QColor(Color.CANVAS_MESH_A))
        base_grad.setColorAt(0.7, QColor(Color.CANVAS_MESH_B))
        base_grad.setColorAt(1.0, QColor(Color.CANVAS_ALT))
        painter.fillRect(self.rect(), base_grad)

        # 2. Radial warm glow in top-left
        radial_tl = QRadialGradient(QPointF(w * 0.15, h * 0.15), max(w, h) * 0.45)
        c_glow = QColor("#EEF2FF")
        c_glow.setAlphaF(0.4)
        c_trans = QColor("#EEF2FF")
        c_trans.setAlphaF(0.0)
        radial_tl.setColorAt(0.0, c_glow)
        radial_tl.setColorAt(1.0, c_trans)
        painter.fillRect(self.rect(), radial_tl)

        painter.end()
