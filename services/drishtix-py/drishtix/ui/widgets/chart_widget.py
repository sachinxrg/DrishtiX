"""
DrishtiX v4.0 — Chart Widgets.

Matplotlib Canvas wrappers styled for the tactical dark theme.
"""

from typing import Dict, List, Optional

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget


class TacticalBarChart(QFrame):
    """Hourly 24-hour detection distribution bar chart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "bento-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Setup dark styled figure
        self.figure = Figure(figsize=(5, 3), dpi=100, facecolor="#1A1D24")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._format_axes()

    def _format_axes(self) -> None:
        self.ax.set_facecolor("#1A1D24")
        self.ax.tick_params(colors="#9AA0A6", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color("#2E3140")
        self.ax.grid(True, linestyle="--", alpha=0.2, color="#9AA0A6")

    def update_data(self, hourly_data: List[Dict[str, int]]) -> None:
        """Render 24-hour bar chart."""
        self.ax.clear()
        self._format_axes()

        hours = [d["hour"] for d in hourly_data]
        counts = [d["count"] for d in hourly_data]

        self.ax.bar(
            hours,
            counts,
            color="#4A9EFF",
            edgecolor="#3B8BE6",
            alpha=0.85,
            width=0.7,
        )

        self.ax.set_title("24-Hour Detection Timeline", color="#E8EAED", fontsize=11, fontweight="bold", pad=8)
        self.ax.set_xlabel("Hour of Day", color="#9AA0A6", fontsize=9)
        self.ax.set_ylabel("Detections", color="#9AA0A6", fontsize=9)
        self.ax.set_xticks(range(0, 24, 3))
        self.figure.tight_layout()
        self.canvas.draw()


class TacticalPieChart(QFrame):
    """Target category breakdown donut chart (Criminal vs Missing)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "bento-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.figure = Figure(figsize=(4, 3), dpi=100, facecolor="#1A1D24")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)

    def update_data(self, category_data: List[Dict[str, object]]) -> None:
        """Render category donut chart."""
        self.ax.clear()
        self.ax.set_facecolor("#1A1D24")

        labels = []
        counts = []
        colors = []

        color_map = {
            "CRIMINAL": "#FF4D2E",
            "MISSING_PERSON": "#00D4FF",
        }

        for item in category_data:
            cat = str(item.get("category", "UNKNOWN")).upper()
            cnt = int(item.get("count", 0))
            if cnt > 0:
                labels.append(cat.replace("_", " "))
                counts.append(cnt)
                colors.append(color_map.get(cat, "#FBBF24"))

        if not counts:
            labels = ["No Data"]
            counts = [1]
            colors = ["#2E3140"]

        wedges, texts, autotexts = self.ax.pie(
            counts,
            labels=labels if counts != [1] else None,
            autopct="%1.1f%%" if counts != [1] else "",
            startangle=140,
            colors=colors,
            textprops={"color": "#E8EAED", "fontsize": 9},
            wedgeprops={"width": 0.5, "edgecolor": "#1A1D24", "linewidth": 2},
        )

        for at in autotexts:
            at.set_color("#0D0F14")
            at.set_fontweight("bold")

        self.ax.set_title("Category Distribution", color="#E8EAED", fontsize=11, fontweight="bold", pad=8)
        self.figure.tight_layout()
        self.canvas.draw()


class TacticalLineChart(QFrame):
    """Daily detection volume trend line chart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "bento-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.figure = Figure(figsize=(6, 3), dpi=100, facecolor="#1A1D24")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._format_axes()

    def _format_axes(self) -> None:
        self.ax.set_facecolor("#1A1D24")
        self.ax.tick_params(colors="#9AA0A6", labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color("#2E3140")
        self.ax.grid(True, linestyle="--", alpha=0.2, color="#9AA0A6")

    def update_data(self, trend_data: List[Dict[str, object]]) -> None:
        """Render daily trend line."""
        self.ax.clear()
        self._format_axes()

        dates = [str(d.get("date", ""))[-5:] for d in trend_data]  # MM-DD
        counts = [int(d.get("count", 0)) for d in trend_data]

        if not dates:
            dates = ["Today"]
            counts = [0]

        self.ax.plot(
            dates,
            counts,
            marker="o",
            color="#34D399",
            linewidth=2,
            markersize=5,
            markerfacecolor="#0D0F14",
            markeredgecolor="#34D399",
            markeredgewidth=2,
        )

        self.ax.fill_between(dates, counts, color="#34D399", alpha=0.15)

        self.ax.set_title("Multi-Day Detection Trend", color="#E8EAED", fontsize=11, fontweight="bold", pad=8)
        self.ax.set_ylabel("Incidents", color="#9AA0A6", fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()
