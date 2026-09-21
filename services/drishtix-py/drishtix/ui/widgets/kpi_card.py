"""
DrishtiX v5.0 — 21st UI KPICard Widget.

Bento-styled metric KPI card with 21st.dev vector iconography,
sparklines, circular progress rings, smooth count-up transitions,
and elevation hover micro-interactions.
"""

import re
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.motion import animate_elevation, animate_number_change, apply_shadow
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Elevation
from drishtix.ui.widgets.circular_progress import CircularProgress
from drishtix.ui.widgets.sparkline import Sparkline


class KPICard(QFrame):
    """
    Bento-styled metric KPI card with 21st UI vector badge and micro-interactions.
    """

    def __init__(
        self,
        title: str,
        initial_value: str = "--",
        icon: Optional[str] = None,
        accent_color: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_class(self, "kpi-card")
        self.setFixedHeight(102)
        self.setMinimumWidth(160)

        self._accent_color = accent_color or Color.ACCENT
        self._sparkline: Optional[Sparkline] = None
        self._progress: Optional[CircularProgress] = None
        self._raw_icon = icon

        # Elevation shadow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        apply_shadow(self._shadow, Elevation.RESTING)
        self.setGraphicsEffect(self._shadow)

        # 21st UI accent border & subtle inner highlight
        self._apply_card_style(hovered=False)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(4)

        # ─── Top Row: Title + 21st UI Icon Badge ────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.lbl_title = QLabel(title.upper())
        apply_class(self.lbl_title, "kpi-title")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()

        if icon:
            self.lbl_icon = QLabel()
            self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_icon.setFixedSize(26, 26)
            self.lbl_icon.setStyleSheet(
                f"background-color: {Color.ACCENT_SOFT}; "
                f"border: 1px solid rgba(62, 86, 224, 0.15); "
                f"border-radius: 7px;"
            )
            # Render vector icon
            pm = render_svg_pixmap(icon, color_hex=self._accent_color, size=15)
            self.lbl_icon.setPixmap(pm)
            top_row.addWidget(self.lbl_icon)

        main_layout.addLayout(top_row)

        # ─── Bottom Row: Value + (Sparkline or Circular Progress) ────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_val = QLabel(initial_value)
        apply_class(self.lbl_val, "kpi-val")
        bottom_row.addWidget(self.lbl_val)
        bottom_row.addStretch()

        # Slot for sparkline / progress
        self._widget_slot = QHBoxLayout()
        self._widget_slot.setContentsMargins(0, 0, 0, 0)
        bottom_row.addLayout(self._widget_slot)

        main_layout.addLayout(bottom_row)

        # Accessibility
        self.setAccessibleName(f"KPI: {title}")
        self.setAccessibleDescription(f"Current value: {initial_value}")

    def set_value(self, value: str, color_hex: Optional[str] = None, animated: bool = False) -> None:
        """Update display value string with optional smooth numerical transition."""
        str_val = str(value)

        if animated:
            old_text = self.lbl_val.text().strip().replace(",", "")
            new_text = str_val.strip().replace(",", "")
            old_match = re.match(r"^([+-]?\d+(?:\.\d+)?)(.*)$", old_text)
            new_match = re.match(r"^([+-]?\d+(?:\.\d+)?)(.*)$", new_text)

            if old_match and new_match and old_match.group(2) == new_match.group(2):
                try:
                    start_val = float(old_match.group(1))
                    end_val = float(new_match.group(1))
                    suffix = new_match.group(2)
                    is_int = "." not in new_match.group(1)

                    def fmt(v: float) -> str:
                        if is_int:
                            return f"{int(v):,}{suffix}"
                        return f"{v:.1f}{suffix}"

                    animate_number_change(self.lbl_val, start_val, end_val, duration_ms=300, formatter=fmt, parent=self)
                except Exception:
                    self.lbl_val.setText(str_val)
            else:
                self.lbl_val.setText(str_val)
        else:
            self.lbl_val.setText(str_val)

        self.setAccessibleDescription(f"Current value: {str_val}")
        if color_hex:
            self.lbl_val.setStyleSheet(f"color: {color_hex};")

    def set_sparkline_data(self, data: List[float], color_hex: Optional[str] = None) -> None:
        """Attach or update an inline Sparkline trend."""
        color = color_hex or self._accent_color
        if self._sparkline is None:
            self._sparkline = Sparkline(data=data, color_hex=color, parent=self)
            self._widget_slot.addWidget(self._sparkline)
        else:
            self._sparkline.set_data(data, color_hex=color)

    def set_progress_ring(self, value: float, max_val: float = 100.0, color_hex: Optional[str] = None) -> None:
        """Attach or update an inline CircularProgress ring."""
        color = color_hex or self._accent_color
        if self._progress is None:
            self._progress = CircularProgress(value=value, max_value=max_val, size=32, thickness=3, color_hex=color, parent=self)
            self._widget_slot.addWidget(self._progress)
        else:
            self._progress.set_value(value, color_hex=color)

    def _apply_card_style(self, hovered: bool = False) -> None:
        """Apply resting or 21st UI illuminated hover styling to card borders and background."""
        if hovered:
            self.setStyleSheet(
                f"QFrame[class=\"kpi-card\"] {{ "
                f"border-left: 4px solid {self._accent_color}; "
                f"border-top: 1px solid rgba(99, 102, 241, 0.45); "
                f"border-right: 1px solid rgba(99, 102, 241, 0.45); "
                f"border-bottom: 1px solid rgba(99, 102, 241, 0.45); "
                f"background-color: {Color.WHITE}; "
                f"border-radius: 12px; "
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"QFrame[class=\"kpi-card\"] {{ "
                f"border-left: 4px solid {self._accent_color}; "
                f"border-top: 1px solid {Color.BORDER_SUBTLE}; "
                f"border-right: 1px solid {Color.BORDER_SUBTLE}; "
                f"border-bottom: 1px solid {Color.BORDER_SUBTLE}; "
                f"background-color: {Color.SURFACE_CARD}; "
                f"border-radius: 12px; "
                f"}}"
            )

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        animate_elevation(self._shadow, Elevation.RAISED)
        self._apply_card_style(hovered=True)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        animate_elevation(self._shadow, Elevation.RESTING)
        self._apply_card_style(hovered=False)
