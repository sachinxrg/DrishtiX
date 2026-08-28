"""
DrishtiX v4.0 — NavButton Widget.

Sidebar navigation button component with active state highlighting.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QWidget


class NavButton(QPushButton):
    """Navigation button for the left command sidebar."""

    def __init__(
        self,
        text: str,
        index: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self.index = index
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setProperty("class", "nav-btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
