"""
DrishtiX v4.0 — BentoGrid Layout System.

12-column grid layout with tile spanning, responsive breakpoints,
and a ResponsiveBentoGrid mixin that all bento-using views inherit.
"""

from typing import Optional

from PySide6.QtWidgets import QFrame, QGridLayout, QVBoxLayout, QWidget

from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Breakpoint, Spacing


class BentoTile(QFrame):
    """
    A single tile in a BentoGrid.

    Wraps a child widget in a QFrame that receives bento-tile QSS styling.
    The tile carries its own span, which `BentoGrid.add_bento_tile()` reads
    so callers don't have to repeat it at placement time.
    """

    def __init__(
        self,
        child: QWidget,
        col_span: int = 1,
        row_span: int = 1,
        variant: str = "bento-tile",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        apply_class(self, variant)
        self.col_span = col_span
        self.row_span = row_span

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(child)


class BentoGrid(QWidget):
    """
    12-column CSS-grid-inspired layout for Qt.

    Usage:
        grid = BentoGrid(columns=12, gap=14)
        grid.add_tile(widget, col=0, col_span=8, row=0, row_span=2)
    """

    def __init__(
        self,
        columns: int = 12,
        gap: int = Spacing.BENTO_GAP,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._columns = columns
        self._gap = gap

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(gap)

        # Set equal column stretches
        for c in range(columns):
            self._grid.setColumnStretch(c, 1)

    @property
    def columns(self) -> int:
        return self._columns

    def set_columns(self, n: int) -> None:
        """Change the number of active columns (for responsive reflow)."""
        self._columns = n
        # Reset all column stretches
        for c in range(self._grid.columnCount()):
            self._grid.setColumnStretch(c, 1 if c < n else 0)

    def add_tile(
        self,
        widget: QWidget,
        col: int = 0,
        col_span: int = 1,
        row: int = 0,
        row_span: int = 1,
    ) -> None:
        """
        Place a widget into the grid at the specified position.

        Args:
            widget: The widget to place.
            col: Starting column (0-indexed).
            col_span: Number of columns to span.
            row: Starting row (0-indexed).
            row_span: Number of rows to span.
        """
        self._grid.addWidget(widget, row, col, row_span, col_span)

    def add_bento_tile(self, tile: BentoTile, col: int = 0, row: int = 0) -> None:
        """
        Place a BentoTile using the span it already carries.

        `add_tile()` ignores a BentoTile's own col_span/row_span, so placing one
        through it silently collapsed the tile to 1x1 unless the caller repeated
        the span by hand.

        Args:
            tile: The tile to place.
            col: Starting column (0-indexed).
            row: Starting row (0-indexed).
        """
        self._grid.addWidget(tile, row, col, tile.row_span, tile.col_span)

    def set_gap(self, gap: int) -> None:
        """Update the gap between tiles."""
        self._gap = gap
        self._grid.setSpacing(gap)

    def grid_layout(self) -> QGridLayout:
        """Access the underlying QGridLayout."""
        return self._grid


class ResponsiveBentoGrid(BentoGrid):
    """
    BentoGrid with automatic responsive reflow.

    All bento-using views should inherit this instead of writing
    their own resizeEvent reflow logic, so all views degrade
    consistently at the same breakpoints.
    """

    def __init__(
        self,
        columns: int = 12,
        gap: int = Spacing.BENTO_GAP,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(columns=columns, gap=gap, parent=parent)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = event.size().width()

        if width < Breakpoint.COMPACT:
            self.set_columns(1)
        elif width < Breakpoint.WIDE:
            self.set_columns(6)
        else:
            self.set_columns(12)
