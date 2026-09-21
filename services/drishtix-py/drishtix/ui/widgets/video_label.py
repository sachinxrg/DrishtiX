"""
DrishtiX v5.0 — VideoLabel Widget.

Aspect-ratio preserving video rendering widget with tactical grid,
corner brackets, and HUD crosshair overlay.
Hard rule: Never attach QGraphicsEffect to VideoLabel.
"""

from typing import Optional

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QLabel, QWidget

from drishtix.ui.style_utils import apply_class


class VideoLabel(QLabel):
    """Aspect-ratio preserved video frame display widget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_class(self, "video-surface")
        self.setMinimumSize(480, 270)
        self._current_pixmap: Optional[QPixmap] = None

    def set_frame(self, pixmap: QPixmap) -> None:
        """Set new video frame and trigger repaint."""
        if not pixmap.isNull():
            self._current_pixmap = pixmap
            self.update()

    def clear_frame(self) -> None:
        """Clear active frame to placeholder."""
        self._current_pixmap = None
        self.update()

    def paintEvent(self, event) -> None:
        """Custom paint for high-DPI scaling, letterboxing, and tactical HUD."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        if self._current_pixmap is not None and not self._current_pixmap.isNull():
            # Scale pixmap maintaining aspect ratio
            scaled = self._current_pixmap.scaled(
                w,
                h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Center pixmap
            x = (w - scaled.width()) // 2
            y = (h - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            # Tactical corner brackets over active video
            c_pen = QPen(QColor(79, 107, 251, 140), 1.5)
            painter.setPen(c_pen)
            b_len = 16

            # Top-Left
            painter.drawLine(x + 8, y + 8, x + 8 + b_len, y + 8)
            painter.drawLine(x + 8, y + 8, x + 8, y + 8 + b_len)
            # Top-Right
            rx = x + scaled.width() - 8
            painter.drawLine(rx, y + 8, rx - b_len, y + 8)
            painter.drawLine(rx, y + 8, rx, y + 8 + b_len)
            # Bottom-Left
            by = y + scaled.height() - 8
            painter.drawLine(x + 8, by, x + 8 + b_len, by)
            painter.drawLine(x + 8, by, x + 8, by - b_len)
            # Bottom-Right
            painter.drawLine(rx, by, rx - b_len, by)
            painter.drawLine(rx, by, rx, by - b_len)

            # Letterbox boundary lines
            painter.setPen(QPen(QColor(79, 107, 251, 40), 1, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, h)
            painter.drawLine(x + scaled.width(), 0, x + scaled.width(), h)

        else:
            # Standby Tactical HUD Placeholder
            painter.setPen(QPen(QColor(51, 65, 85), 1.2, Qt.PenStyle.SolidLine))

            # Center Crosshair with target ring
            cx, cy = w // 2, h // 2
            arm = 28
            painter.drawLine(cx - arm, cy, cx - 8, cy)
            painter.drawLine(cx + 8, cy, cx + arm, cy)
            painter.drawLine(cx, cy - arm, cx, cy - 8)
            painter.drawLine(cx, cy + 8, cx, cy + arm)
            painter.drawEllipse(QPoint(cx, cy), 18, 18)
            painter.drawEllipse(QPoint(cx, cy), 6, 6)

            # Corner brackets for empty HUD
            c_pen = QPen(QColor(79, 107, 251, 70), 1.5)
            painter.setPen(c_pen)
            b_len = 24
            m = 16
            painter.drawLine(m, m, m + b_len, m)
            painter.drawLine(m, m, m, m + b_len)
            painter.drawLine(w - m, m, w - m - b_len, m)
            painter.drawLine(w - m, m, w - m, m + b_len)
            painter.drawLine(m, h - m, m + b_len, h - m)
            painter.drawLine(m, h - m, m, h - m - b_len)
            painter.drawLine(w - m, h - m, w - m - b_len, h - m)
            painter.drawLine(w - m, h - m, w - m, h - m - b_len)

            # Placeholder Text
            painter.setPen(QPen(QColor(226, 232, 240), 1))
            painter.setFont(QFont("Inter", 12, QFont.Weight.DemiBold))
            painter.drawText(
                QRect(0, cy + 34, w, 36),
                Qt.AlignmentFlag.AlignCenter,
                "AWAITING VIDEO STREAM",
            )
            painter.setFont(QFont("Inter", 9))
            painter.setPen(QPen(QColor(148, 163, 184), 1))
            painter.drawText(
                QRect(0, cy + 68, w, 26),
                Qt.AlignmentFlag.AlignCenter,
                "Connect a camera device or RTSP stream in Settings",
            )

        painter.end()
