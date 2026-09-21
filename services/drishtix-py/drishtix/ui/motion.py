"""
DrishtiX v5.0 — 21st UI Motion & Interaction System.

Advanced micro-interactions, spring/cubic-bezier transitions, and animations:
- QPropertyAnimation-driven elevation transitions for GlassCard hover/press
- FadingStackedWidget for smooth cross-fade view switching
- PulsingStatusDot for 21st UI live radar / breathing status indicators
- Numerical count-up interpolator for telemetry & KPI metrics
- Respects OS reduced-motion preferences via QStyleHints
"""

from typing import Callable, Optional

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRectF,
    QSize,
    QTimer,
    QVariantAnimation,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLabel,
    QStackedWidget,
    QWidget,
)

from drishtix.ui.theme_tokens import Color, ShadowPreset


def _is_motion_reduced() -> bool:
    """Report whether the OS asks for reduced motion."""
    app = QApplication.instance()
    if app is None:
        return False
    try:
        hints = app.styleHints()
        probe = getattr(hints, "isMotionReduced", None)
        return bool(probe()) if callable(probe) else False
    except (AttributeError, RuntimeError):
        return False


# ─── 1. ELEVATION & SHADOW TRANSITIONS ──────────────────────────────────────

def animate_elevation(
    effect: QGraphicsDropShadowEffect,
    preset: ShadowPreset,
    duration_ms: int = 160,
) -> Optional[QPropertyAnimation]:
    """
    Animate a drop shadow effect to a new elevation tier with smooth easing.
    """
    if _is_motion_reduced():
        apply_shadow(effect, preset)
        return None

    effect.setOffset(0, preset.y_offset)
    shadow_color = QColor(0, 0, 0)
    shadow_color.setAlphaF(preset.alpha)
    effect.setColor(shadow_color)

    anim = QPropertyAnimation(effect, b"blurRadius", effect)
    anim.setDuration(duration_ms)
    anim.setEndValue(preset.blur)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def apply_shadow(
    effect: QGraphicsDropShadowEffect,
    preset: ShadowPreset,
) -> None:
    """Set a drop shadow to match an elevation preset (no animation)."""
    effect.setBlurRadius(preset.blur)
    effect.setOffset(0, preset.y_offset)
    shadow_color = QColor(0, 0, 0)
    shadow_color.setAlphaF(preset.alpha)
    effect.setColor(shadow_color)


# ─── 2. FADING STACKED WIDGET (21st UI View Transitions) ───────────────────

class FadingStackedWidget(QStackedWidget):
    """
    QStackedWidget replacement featuring smooth cross-fade transitions.

    When setCurrentIndex() is called, the outgoing page fades out and the
    incoming page smoothly cross-fades into view with an OutCubic curve.
    """

    def __init__(self, parent: Optional[QWidget] = None, duration_ms: int = 220) -> None:
        super().__init__(parent)
        self._duration_ms = duration_ms
        self._anim: Optional[QPropertyAnimation] = None

    def setCurrentIndex(self, index: int) -> None:
        if index == self.currentIndex() or index < 0 or index >= self.count():
            return

        if _is_motion_reduced():
            super().setCurrentIndex(index)
            return

        next_widget = self.widget(index)
        if next_widget is None:
            super().setCurrentIndex(index)
            return

        # Prepare incoming widget with opacity effect
        effect = QGraphicsOpacityEffect(next_widget)
        effect.setOpacity(0.0)
        next_widget.setGraphicsEffect(effect)

        super().setCurrentIndex(index)

        self._anim = QPropertyAnimation(effect, b"opacity", self)
        self._anim.setDuration(self._duration_ms)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_finished():
            # Clear effect when animation completes to free GPU/compositor memory
            next_widget.setGraphicsEffect(None)

        self._anim.finished.connect(_on_finished)
        self._anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ─── 3. PULSING STATUS DOT (21st UI Live Radar Indicator) ───────────────────

class PulsingStatusDot(QWidget):
    """
    Live status indicator with 21st UI animated breathing ripple aura.

    Paints a centered solid status dot surrounded by an expanding, fading
    concentric ring representing live camera feed or active perimeter state.
    """

    def __init__(
        self,
        color_hex: str = Color.SAFE,
        dot_radius: float = 4.0,
        max_aura_radius: float = 9.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color_hex)
        self._dot_radius = dot_radius
        self._max_aura_radius = max_aura_radius
        self._aura_progress = 0.0  # 0.0 to 1.0

        size = int(max_aura_radius * 2 + 4)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1600)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)  # Infinite breathing loop
        self._anim.valueChanged.connect(self._on_anim_frame)

        if not _is_motion_reduced():
            self._anim.start()

    def set_color(self, color_hex: str) -> None:
        """Update indicator color (e.g. green for safe, red for critical)."""
        self._color = QColor(color_hex)
        self.update()

    def _on_anim_frame(self, val: float) -> None:
        self._aura_progress = float(val)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        # 1. Concentric Aura Ripple (expanding & fading)
        if not _is_motion_reduced() and self._aura_progress > 0.01:
            aura_r = self._dot_radius + (self._max_aura_radius - self._dot_radius) * self._aura_progress
            aura_alpha = (1.0 - self._aura_progress) * 0.45

            aura_color = QColor(self._color)
            aura_color.setAlphaF(aura_alpha)

            painter.setBrush(aura_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - aura_r, cy - aura_r, aura_r * 2, aura_r * 2))

        # 2. Solid Core Dot
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        r = self._dot_radius
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        painter.end()


# ─── 4. NUMBER COUNTER ANIMATION ───────────────────────────────────────────

def animate_number_change(
    label: QLabel,
    start_val: float,
    end_val: float,
    duration_ms: int = 350,
    formatter: Optional[Callable[[float], str]] = None,
    parent: Optional[QObject] = None,
) -> Optional[QVariantAnimation]:
    """
    Interpolate a numerical value smoothly in a QLabel.
    """
    if _is_motion_reduced() or abs(end_val - start_val) < 0.001:
        fmt = formatter or (lambda v: f"{int(v)}" if v.is_integer() else f"{v:.1f}")
        label.setText(fmt(end_val))
        return None

    anim = QVariantAnimation(parent or label)
    anim.setDuration(duration_ms)
    anim.setStartValue(float(start_val))
    anim.setEndValue(float(end_val))
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    fmt = formatter or (lambda v: f"{int(v):,}" if v.is_integer() else f"{v:.1f}")

    def _on_step(val: float):
        label.setText(fmt(float(val)))

    anim.valueChanged.connect(_on_step)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


# ─── 5. SLIDING INDICATOR PILL (21st UI Tab Indicator) ─────────────────────

class SlidingIndicatorPill(QFrame):
    """
    21st UI Framer-Motion style sliding pill indicator.

    Glides smoothly behind or over active navigation items with OutCubic easing
    and high-performance geometry interpolation.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        duration_ms: int = 220,
        gradient_start: str = Color.ACCENT_GRADIENT_START,
        gradient_end: str = Color.ACCENT_GRADIENT_END,
        border_radius: int = 12,
    ) -> None:
        super().__init__(parent)
        self._duration_ms = duration_ms
        self._anim: Optional[QPropertyAnimation] = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.setStyleSheet(
            f"QFrame {{ "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {gradient_start}, stop:1 {gradient_end}); "
            f"border-radius: {border_radius}px; "
            f"border: none; "
            f"}}"
        )
        self.hide()

    def glide_to(self, target_widget: QWidget, animate: bool = True) -> None:
        """Glide smoothly to the geometry of target_widget."""
        if not target_widget:
            return

        target_geom = target_widget.geometry()
        if target_geom.isEmpty():
            return

        self.show()
        self.stackUnder(target_widget)

        if not animate or _is_motion_reduced():
            self.setGeometry(target_geom)
            return

        if self._anim and self._anim.state() == QAbstractAnimation.State.Running:
            self._anim.stop()

        start_geom = self.geometry()
        if start_geom.isEmpty() or not self.isVisible():
            start_geom = target_geom

        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(self._duration_ms)
        self._anim.setStartValue(start_geom)
        self._anim.setEndValue(target_geom)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

