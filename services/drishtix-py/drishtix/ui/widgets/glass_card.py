"""
DrishtiX v5.0 — GlassCard Widget.

Glassmorphic card container with typed variants, tiered elevation shadows,
and hover animation integration via the motion system.
"""

from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from drishtix.ui.motion import animate_elevation, apply_shadow
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Elevation


class CardVariant(Enum):
    """Glass card visual variants mapped to QSS class names."""
    GLASS       = "glass-card"
    GLASS_HEAVY = "glass-card-heavy"
    ELEVATED    = "glass-card-elevated"
    NEU_RAISED  = "neu-raised"
    NEU_INSET   = "neu-inset"


class GlassCard(QFrame):
    """
    Glassmorphic card container.

    Supports visual variants and a 4-tier elevation system
    (resting → raised → overlay) with animated transitions.
    """

    def __init__(
        self,
        variant: CardVariant = CardVariant.GLASS,
        enable_hover: bool = True,
        title: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._variant = variant
        self._enable_hover = enable_hover

        # Apply QSS class
        apply_class(self, variant.value)

        # Internal layout for child content
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

        if title:
            lbl_hdr = QLabel(title)
            apply_class(lbl_hdr, "type-h3")
            self._layout.addWidget(lbl_hdr)

        # Drop shadow effect — resting elevation
        self._shadow = QGraphicsDropShadowEffect(self)
        apply_shadow(self._shadow, Elevation.RESTING)
        self.setGraphicsEffect(self._shadow)

    def content_layout(self) -> QVBoxLayout:
        """Access the internal layout to add child widgets."""
        return self._layout

    def set_variant(self, variant: CardVariant) -> None:
        """Switch the card's visual variant at runtime."""
        self._variant = variant
        apply_class(self, variant.value)

    def set_accent_border(self, color_hex: str, width: int = 4) -> None:
        """Add a color-coded left accent border to the card."""
        self.setStyleSheet(
            f"QFrame[class~=\"{self._variant.value}\"] {{ border-left: {width}px solid {color_hex}; }}"
        )

    def enterEvent(self, event) -> None:
        """Elevate shadow on hover."""
        super().enterEvent(event)
        if self._enable_hover:
            animate_elevation(self._shadow, Elevation.RAISED)

    def leaveEvent(self, event) -> None:
        """Return shadow to resting on leave."""
        super().leaveEvent(event)
        if self._enable_hover:
            animate_elevation(self._shadow, Elevation.RESTING)

    def set_accessible_info(self, name: str, description: str = "") -> None:
        """Set QAccessible name and description for screen readers."""
        self.setAccessibleName(name)
        if description:
            self.setAccessibleDescription(description)
