"""
DrishtiX v5.0 — TimelineStrip Widget.

Horizontal timeline event strip displaying surveillance detections chronologically.
Each incident is marked with an interactive marker colored by category with match metadata tooltips.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from drishtix.ui.theme_tokens import Color


class TimelineStrip(QWidget):
    """
    Chronological detection event timeline.

    Plots detection events across the last N hours on a horizontal time axis.
    """

    def __init__(
        self,
        events: Optional[List[Dict[str, object]]] = None,
        hours_window: int = 4,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setMouseTracking(True)
        self._hours_window = hours_window
        self._events: List[Dict[str, object]] = events if events else []

    def set_events(self, events: List[Dict[str, object]]) -> None:
        """Update timeline events list."""
        self._events = events
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        y_axis = h / 2.0

        # 1. Base Axis Line
        painter.setPen(QPen(QColor(Color.BORDER_SUBTLE), 2.0, Qt.PenStyle.SolidLine))
        painter.drawLine(10, int(y_axis), int(w - 10), int(y_axis))

        now = datetime.now()
        window_start = now - timedelta(hours=self._hours_window)
        total_seconds = self._hours_window * 3600.0

        # 2. Time Marks (Beginning, Middle, Now)
        painter.setFont(QFont("Inter", 8, QFont.Weight.Medium))
        painter.setPen(QPen(QColor(Color.TEXT_MUTED)))

        painter.drawText(QRectF(10, y_axis + 4, 80, 14), Qt.AlignmentFlag.AlignLeft, f"-{self._hours_window}h")
        painter.drawText(QRectF(w - 70, y_axis + 4, 60, 14), Qt.AlignmentFlag.AlignRight, "NOW")

        # 3. Plot Event Markers
        for ev in self._events:
            ts: Optional[datetime] = ev.get("timestamp")
            if not ts or not isinstance(ts, datetime):
                continue
            if ts < window_start or ts > now:
                continue

            sec_offset = (ts - window_start).total_seconds()
            x = 20.0 + (sec_offset / total_seconds) * (w - 40.0)

            is_crim = "CRIM" in str(ev.get("category", "")).upper()
            color = QColor(Color.CRITICAL) if is_crim else QColor(Color.INFO)

            # Draw outer ring & dot
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(x), int(y_axis)), 4, 4)

        painter.end()

    def mouseMoveEvent(self, event) -> None:
        pos = event.pos()
        w = self.width()
        now = datetime.now()
        window_start = now - timedelta(hours=self._hours_window)
        total_seconds = self._hours_window * 3600.0

        for ev in self._events:
            ts: Optional[datetime] = ev.get("timestamp")
            if not ts or not isinstance(ts, datetime):
                continue
            sec_offset = (ts - window_start).total_seconds()
            x = 20.0 + (sec_offset / total_seconds) * (w - 40.0)

            if abs(pos.x() - x) <= 8 and abs(pos.y() - self.height() / 2.0) <= 10:
                name = ev.get("full_name", "Unknown")
                cat = ev.get("category", "N/A")
                conf = ev.get("confidence", 0.0)
                time_str = ts.strftime("%H:%M:%S")
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"🎯 {name} ({cat})\n📊 Match: {conf * 100:.1f}%\n🕒 {time_str}",
                    self,
                )
                return
        QToolTip.hideText()
