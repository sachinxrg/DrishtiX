"""
DrishtiX v4.0 — VideoLabel Widget.

Aspect-ratio preserving video rendering widget with tactical grid and crosshair overlay.
"""

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QWidget


class VideoLabel(QLabel):
    """Aspect-ratio preserved video frame display widget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #07090C; border-radius: 6px;")
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

            # Draw subtle tactical grid lines over letterbox borders
            painter.setPen(QPen(QColor(46, 49, 64, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, h)
            painter.drawLine(x + scaled.width(), 0, x + scaled.width(), h)

        else:
            # Standby Tactical HUD Placeholder
            painter.setPen(QPen(QColor(30, 33, 45), 1, Qt.PenStyle.SolidLine))

            # Center Crosshair
            cx, cy = w // 2, h // 2
            arm = 24
            painter.drawLine(cx - arm, cy, cx + arm, cy)
            painter.drawLine(cx, cy - arm, cx, cy + arm)
            painter.drawEllipse(QPoint(cx, cy), 16, 16)

            # Placeholder Text
            painter.setPen(QPen(QColor(154, 160, 166), 1))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
            painter.drawText(
                QRect(0, cy + 30, w, 40),
                Qt.AlignmentFlag.AlignCenter,
                "AWAITING VIDEO STREAM",
            )
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QPen(QColor(85, 90, 101), 1))
            painter.drawText(
                QRect(0, cy + 65, w, 30),
                Qt.AlignmentFlag.AlignCenter,
                "Connect a camera device or RTSP stream in Settings",
            )
