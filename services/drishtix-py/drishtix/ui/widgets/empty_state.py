"""
DrishtiX v5.0 — 21st UI EmptyStateWidget.

Reusable empty/zero-data state panel with 21st.dev vector iconography,
frosted container styling, active-voice messaging, and action buttons.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color


class _EmptyStateIconLabel(QLabel):
    """
    Dual-mode icon label that renders crisp 21st UI vector graphics
    while preserving string text queries for testing.
    """

    def __init__(self, icon_str: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._raw_icon = icon_str
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(56, 56)
        self.setStyleSheet(
            f"background-color: {Color.ACCENT_SOFT}; "
            f"border: 1px solid rgba(62, 86, 224, 0.12); "
            f"border-radius: 28px; "
            f"padding: 10px;"
        )
        self._update_pixmap()

    def _update_pixmap(self) -> None:
        pm = render_svg_pixmap(self._raw_icon, color_hex=Color.ACCENT, size=32)
        if not pm.isNull():
            self.setPixmap(pm)

    def text(self) -> str:
        return self._raw_icon

    def setText(self, text: str) -> None:
        self._raw_icon = text
        self._update_pixmap()


class EmptyStateWidget(QFrame):
    """
    Empty state panel for views/sections with no data.

    Displays a 21st UI vector badge, human-readable message, and optional
    action button to guide the operator toward resolving the empty state.
    """

    def __init__(
        self,
        icon: str = "📭",
        message: str = "Nothing here yet",
        action_text: str = "",
        action_callback=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_class(self, "empty-state")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(32, 32, 32, 32)

        # 21st UI Vector Icon Badge
        self._lbl_icon = _EmptyStateIconLabel(icon, self)
        apply_class(self._lbl_icon, "empty-state-icon")
        layout.addWidget(self._lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # Message
        self._lbl_message = QLabel(message)
        self._lbl_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_message.setWordWrap(True)
        apply_class(self._lbl_message, "empty-state-message")
        layout.addWidget(self._lbl_message)

        # Action button
        self._btn_action = QPushButton(action_text)
        apply_class(self._btn_action, "btn-primary")
        self._btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        if action_callback:
            self._btn_action.clicked.connect(action_callback)
        self._btn_action.setVisible(bool(action_text))
        layout.addWidget(self._btn_action, alignment=Qt.AlignmentFlag.AlignCenter)

        # Accessibility
        self.setAccessibleName("Empty state")
        self.setAccessibleDescription(message.replace("\n", " "))

    def set_message(self, message: str) -> None:
        """Update the empty state message."""
        self._lbl_message.setText(message)
        self.setAccessibleDescription(message.replace("\n", " "))

    def set_icon(self, icon: str) -> None:
        """Update the empty state icon."""
        self._lbl_icon.setText(icon)

    def set_action(self, action_text: str, action_callback=None) -> None:
        """Set or replace the action button label and handler."""
        self._btn_action.setText(action_text)
        if action_callback is not None:
            try:
                self._btn_action.clicked.disconnect()
            except RuntimeError:
                pass
            self._btn_action.clicked.connect(action_callback)
        self._btn_action.setVisible(bool(action_text))
