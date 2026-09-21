"""
DrishtiX v5.0 — Chart Widgets.

Matplotlib Canvas wrappers styled for the light glassmorphic theme.
Re-themed via design tokens, with transparent patch backgrounds and draw_idle().
"""

from typing import Dict, List, Optional

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard

matplotlib.use("QtAgg")


class TacticalBarChart(GlassCard):
    """Hourly 24-hour detection distribution bar chart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(variant=CardVariant.GLASS, enable_hover=True, parent=parent)

        layout = self.content_layout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Setup light styled figure with transparent patch for GlassCard nesting
        self.figure = Figure(figsize=(5, 3), dpi=100, facecolor="none")
        self.figure.patch.set_alpha(0.0)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._format_axes()

    def _format_axes(self) -> None:
        self.ax.set_facecolor("none")
        self.ax.patch.set_alpha(0.0)
        self.ax.tick_params(colors=Color.TEXT_SECONDARY, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(Color.BORDER_SUBTLE)
        self.ax.grid(True, linestyle="--", alpha=0.35, color=Color.BORDER_MUTED)

    def update_data(self, hourly_data: List[Dict[str, int]]) -> None:
        """Render 24-hour bar chart."""
        self.ax.clear()
        self._format_axes()

        hours = [d["hour"] for d in hourly_data]
        counts = [d["count"] for d in hourly_data]

        self.ax.bar(
            hours,
            counts,
            color=Color.ACCENT,
            edgecolor=Color.ACCENT_HOVER,
            alpha=0.88,
            width=0.68,
        )

        self.ax.set_title("24-Hour Detection Timeline", color=Color.TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=8)
        self.ax.set_xlabel("Hour of Day", color=Color.TEXT_SECONDARY, fontsize=9)
        self.ax.set_ylabel("Detections", color=Color.TEXT_SECONDARY, fontsize=9)
        self.ax.set_xticks(range(0, 24, 3))
        self.figure.tight_layout()
        self.canvas.draw_idle()


class TacticalPieChart(GlassCard):
    """Target category breakdown donut chart (Criminal vs Missing)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(variant=CardVariant.GLASS, enable_hover=True, parent=parent)

        layout = self.content_layout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.figure = Figure(figsize=(4, 3), dpi=100, facecolor="none")
        self.figure.patch.set_alpha(0.0)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)

    def update_data(self, category_data: List[Dict[str, object]]) -> None:
        """Render category donut chart."""
        self.ax.clear()
        self.ax.set_facecolor("none")
        self.ax.patch.set_alpha(0.0)

        labels = []
        counts = []
        colors = []

        color_map = {
            "CRIMINAL": Color.CRITICAL,
            "MISSING_PERSON": Color.INFO,
        }

        for item in category_data:
            cat = str(item.get("category", "UNKNOWN")).upper()
            cnt = int(item.get("count", 0))
            if cnt > 0:
                labels.append(cat.replace("_", " "))
                counts.append(cnt)
                colors.append(color_map.get(cat, Color.WARNING))

        if not counts:
            labels = ["No Data"]
            counts = [1]
            colors = [Color.BORDER_SUBTLE]

        wedges, texts, autotexts = self.ax.pie(
            counts,
            labels=labels if counts != [1] else None,
            autopct="%1.1f%%" if counts != [1] else "",
            startangle=140,
            colors=colors,
            textprops={"color": Color.TEXT_BODY, "fontsize": 9},
            wedgeprops={"width": 0.48, "edgecolor": Color.CANVAS, "linewidth": 2},
        )

        for at in autotexts:
            at.set_color(Color.WHITE)
            at.set_fontweight("bold")

        self.ax.set_title("Category Distribution", color=Color.TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=8)
        self.figure.tight_layout()
        self.canvas.draw_idle()


class TacticalLineChart(GlassCard):
    """Daily detection volume trend line chart."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(variant=CardVariant.GLASS, enable_hover=True, parent=parent)

        layout = self.content_layout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.figure = Figure(figsize=(6, 3), dpi=100, facecolor="none")
        self.figure.patch.set_alpha(0.0)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._format_axes()

    def _format_axes(self) -> None:
        self.ax.set_facecolor("none")
        self.ax.patch.set_alpha(0.0)
        self.ax.tick_params(colors=Color.TEXT_SECONDARY, labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(Color.BORDER_SUBTLE)
        self.ax.grid(True, linestyle="--", alpha=0.35, color=Color.BORDER_MUTED)

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
            color=Color.SAFE,
            linewidth=2.2,
            markersize=5.5,
            markerfacecolor=Color.WHITE,
            markeredgecolor=Color.SAFE,
            markeredgewidth=2,
        )

        self.ax.fill_between(dates, counts, color=Color.SAFE, alpha=0.12)

        self.ax.set_title("Multi-Day Detection Trend", color=Color.TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=8)
        self.ax.set_ylabel("Incidents", color=Color.TEXT_SECONDARY, fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw_idle()
