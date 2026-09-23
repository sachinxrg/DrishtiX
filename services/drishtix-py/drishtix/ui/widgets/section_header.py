"""
DrishtiX v5.0 — 21st UI SectionHeader Widget.

Reusable view title + optional subtitle + action widget slot.
Applies the 21st UI typography scale and crisp vector category iconography.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color


class SectionHeader(QWidget):
    """
    View section header with title, optional subtitle, 21st UI vector icon, and action slot.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(12)

        # Title block
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_block.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if icon:
            lbl_icon = QLabel()
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_icon.setFixedSize(28, 28)
            lbl_icon.setStyleSheet(
                f"background-color: {Color.ACCENT_SOFT}; "
                f"border: 1px solid rgba(62, 86, 224, 0.15); "
                f"border-radius: 8px;"
            )
            pm = render_svg_pixmap(icon, Color.ACCENT, 16)
            if not pm.isNull():
                lbl_icon.setPixmap(pm)
            else:
                lbl_icon.setText(icon)
            title_row.addWidget(lbl_icon)

        self._lbl_title = QLabel(title)
        apply_class(self._lbl_title, "type-h1")
        self._lbl_title.setAccessibleName(title)
        title_row.addWidget(self._lbl_title)
        title_row.addStretch()

        title_block.addLayout(title_row)

        self._lbl_subtitle = QLabel(subtitle)
        apply_class(self._lbl_subtitle, "type-caption")
        self._lbl_subtitle.setVisible(bool(subtitle))
        title_block.addWidget(self._lbl_subtitle)

        layout.addLayout(title_block)
        layout.addStretch()

        # Action slot (right side)
        self._action_layout = QHBoxLayout()
        self._action_layout.setSpacing(8)
        layout.addLayout(self._action_layout)

    def add_action(self, widget: QWidget) -> None:
        """Add an action widget (button, badge, etc.) to the right side."""
        self._action_layout.addWidget(widget)

    def set_title(self, text: str) -> None:
        """Update the title text."""
        self._lbl_title.setText(text)
        self._lbl_title.setAccessibleName(text)

    def set_subtitle(self, text: str) -> None:
        """Update the subtitle text, hiding the label when empty."""
        self._lbl_subtitle.setText(text)
        self._lbl_subtitle.setVisible(bool(text))
