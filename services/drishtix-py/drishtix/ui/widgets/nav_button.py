"""
DrishtiX v5.0 — 21st UI NavButton Widget.

Sidebar navigation button component with 21st.dev vector iconography,
smooth hover lighting, and active state accent pill highlighting.
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton, QWidget

from drishtix.ui.icons import render_svg_icon
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color


class NavButton(QPushButton):
    """Navigation button for the left command sidebar with 21st UI styling."""

    def __init__(
        self,
        text: str,
        index: int,
        icon_text: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(f"  {text}", parent)
        self.index = index
        self._raw_text = text
        self._icon_key = icon_text

        self.setCheckable(True)
        self.setAutoExclusive(True)
        apply_class(self, "nav-btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)

        # 21st UI SVG Vector Icon with state-aware coloring
        if icon_text:
            svg_icon = render_svg_icon(
                icon_text,
                normal_color=Color.TEXT_SECONDARY,
                active_color=Color.WHITE,
                hover_color=Color.ACCENT,
                size=18,
            )
            self.setIcon(svg_icon)
            self.setIconSize(QSize(18, 18))
