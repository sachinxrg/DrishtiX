"""
DrishtiX v4.0 — PillBadge Widget.

Semantic status pill badges that replace all hand-coded capsule styles.
Runtime status changes use apply_class() for proper QSS re-evaluation.
"""

from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from drishtix.ui.style_utils import apply_class


class PillStatus(Enum):
    """Pill badge semantic statuses mapped to QSS class names."""
    LIVE     = "pill-live"
    OFFLINE  = "pill-offline"
    SAFE     = "pill-safe"
    WARNING  = "pill-warning"
    CRITICAL = "pill-critical"
    INFO     = "pill-info"
    ACCENT   = "pill-accent"
    NEUTRAL  = "pill-neutral"


# Convenience mapping for StatusBar capsule variants
CAPSULE_STATUS_MAP = {
    "safe":     "status-capsule-safe",
    "warning":  "status-capsule-warning",
    "critical": "status-capsule-critical",
    "info":     "status-capsule-info",
    "neutral":  "status-capsule-neutral",
    "accent":   "status-capsule-accent",
}


class PillBadge(QLabel):
    """
    Semantic status pill badge.

    Replaces all hand-coded capsule setStyleSheet calls with
    QSS class-driven styling.

    Usage:
        pill = PillBadge("● LIVE FEED", PillStatus.LIVE)
        pill.set_status(PillStatus.OFFLINE)
        pill.set_text("● OFFLINE")
    """

    def __init__(
        self,
        text: str = "",
        status: PillStatus = PillStatus.NEUTRAL,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self._status = status
        apply_class(self, status.value)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAccessibleName(text)

    def set_status(self, status: PillStatus) -> None:
        """Change the pill's semantic status and re-apply QSS."""
        # Same reasoning as StatusCapsule.set_capsule_status: apply_class()
        # is a full style recomputation, and callers such as the alert
        # sidebar's count badge re-assert the same status repeatedly.
        if status == self._status:
            return
        self._status = status
        apply_class(self, status.value)

    def set_text(self, text: str) -> None:
        """Update the pill's display text."""
        self.setText(text)
        self.setAccessibleName(text)

    @property
    def status(self) -> PillStatus:
        return self._status


class StatusCapsule(QLabel):
    """
    Inline status capsule for the StatusBar.

    Uses the status-capsule-* QSS classes for consistent styling
    without inline setStyleSheet calls.

    Usage:
        capsule = StatusCapsule("● SYSTEM READY", "safe")
        capsule.set_capsule_status("critical")
    """

    def __init__(
        self,
        text: str = "",
        status: str = "neutral",
        monospace: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self._capsule_status = status
        self._monospace = monospace
        self._apply_capsule_class()
        self.setAccessibleName(text)

    def _apply_capsule_class(self) -> None:
        # Monospace is an orthogonal `mono` property, not a "-mono" class
        # suffix. The suffix approach needed a hand-written twin of every
        # status rule and the QSS only ever had status-capsule-neutral-mono,
        # so a monospace capsule in any other status matched no rule at all
        # and lost its background, border, padding and colour. The FPS
        # capsule hit this on every frame: it starts neutral+mono, then
        # _on_fps_updated switches it to safe/warning/critical.
        class_name = CAPSULE_STATUS_MAP.get(self._capsule_status, "status-capsule-neutral")
        self.setProperty("mono", self._monospace)
        apply_class(self, class_name)  # triggers the unpolish/polish repaint

    def set_capsule_status(self, status: str) -> None:
        """Change the capsule's status and re-apply QSS."""
        # apply_class() forces a full unpolish/polish style recomputation, so
        # skip it when nothing changed. The FPS capsule is driven by
        # fps_updated, which fires every 0.5s for the whole session while the
        # status itself almost never moves.
        if status == self._capsule_status:
            return
        self._capsule_status = status
        self._apply_capsule_class()

    def set_text(self, text: str) -> None:
        """Update the capsule's display text."""
        self.setText(text)
        self.setAccessibleName(text)
