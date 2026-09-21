"""
DrishtiX v4.0 — Style Utilities.

Central styling helpers that ensure QSS property-based selectors
actually fire by running the unpolish/polish cycle.
"""

from PySide6.QtWidgets import QWidget


def apply_class(widget: QWidget, class_name: str) -> None:
    """
    Set a QSS class on a widget and force the style engine to re-evaluate.

    Qt's property-based selectors (e.g. QFrame[class="glass-card"]) require
    an explicit unpolish/polish cycle after setProperty — without it, the
    selector silently fails to match. This is the single highest-leverage
    fix in the entire design-system migration.

    Args:
        widget: The widget to restyle.
        class_name: The QSS class name to apply (e.g. "glass-card", "pill-live").
    """
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def apply_status(widget: QWidget, status: str) -> None:
    """
    Set a QSS status property and force re-evaluation.

    Used for runtime status changes on PillBadge and StatusBar capsules.

    Args:
        widget: The widget to restyle.
        status: The status value (e.g. "safe", "warning", "critical").
    """
    widget.setProperty("status", status)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def remove_class(widget: QWidget) -> None:
    """
    Remove any QSS class from a widget and force re-evaluation.

    Args:
        widget: The widget to clear styling from.
    """
    widget.setProperty("class", None)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
