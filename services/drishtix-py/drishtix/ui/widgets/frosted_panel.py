"""
DrishtiX v4.0 — FrostedPanel (Real Blur Engine).

Renders a blurred snapshot of the widget behind it, rebuilt only on
resize/move — never per frame — so it never touches the video feed's
or alert list's paint budget.

Scope: sidebar and modal backdrop ONLY.
Performance: O(1) per resize/move event, debounced at 120ms.
Hard rule: NEVER attach to VideoLabel or ScrollArea list items.
"""

from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QWidget,
)


class FrostedPanel(QWidget):
    """
    Real frosted glass panel that blurs the content behind it.

    Captures a snapshot of the target widget, applies a Gaussian blur
    via QGraphicsScene/QGraphicsBlurEffect, and caches the result.
    The cache is rebuilt on resize/move with a 120ms debounce timer,
    so it never repaints per-frame.

    Usage:
        frosted = FrostedPanel(target=content_widget, blur_radius=24)
        # Place frosted as an overlay/backdrop behind your sidebar
    """

    def __init__(
        self,
        target: QWidget,
        blur_radius: int = 24,
        tint_alpha: int = 180,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._target = target
        self._blur_radius = blur_radius
        self._tint_alpha = tint_alpha
        self._cache: Optional[QPixmap] = None

        # Debounced rebuild timer — 120ms after last resize/move
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(120)
        self._refresh_timer.timeout.connect(self._rebuild_cache)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_timer.start()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        self._refresh_timer.start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_timer.start()

    def invalidate_cache(self) -> None:
        """Force a cache rebuild on next paint."""
        self._cache = None
        self._refresh_timer.start()

    def _rebuild_cache(self) -> None:
        """Capture target widget snapshot and apply blur."""
        if not self._target or not self._target.isVisible():
            self._cache = None
            self.update()
            return

        try:
            snapshot = self._target.grab(self._target.rect())
            if snapshot.isNull():
                self._cache = None
            else:
                self._cache = self._apply_blur(snapshot, self._blur_radius)
        except RuntimeError:
            self._cache = None

        self.update()

    def _apply_blur(self, pixmap: QPixmap, radius: int) -> QPixmap:
        """Apply Gaussian blur via QGraphicsScene (offscreen render)."""
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(radius)
        item.setGraphicsEffect(blur)
        scene.addItem(item)

        result = QPixmap(pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        scene.render(painter)
        painter.end()
        return result

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self._cache and not self._cache.isNull():
            # Draw blurred backdrop
            painter.drawPixmap(0, 0, self._cache.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            # White tint overlay for the frosted glass look
            painter.fillRect(
                self.rect(),
                QColor(255, 255, 255, self._tint_alpha),
            )
        else:
            # Fallback: the solid semi-transparent white IS the tint while the
            # first snapshot builds — filling twice would stack the alpha and
            # render the panel almost opaque.
            painter.fillRect(self.rect(), QColor(255, 255, 255, self._tint_alpha))

        painter.end()
