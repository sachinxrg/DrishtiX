"""
DrishtiX v4.0 — UI Component & Design System Unit Tests.

Validates:
  1. apply_class() / apply_status() unpolish/polish lifecycle execution.
  2. BentoGrid, BentoTile and ResponsiveBentoGrid column reflow math.
  3. PillBadge and StatusCapsule semantic status mappings.
  4. GlassCard variants and drop shadow attachments.
  5. EmptyStateWidget and SectionHeader composition (including optional parts).
  6. Theme tokens and QSS synchronization.
"""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QWidget

from drishtix.ui.style_utils import apply_class, apply_status
from drishtix.ui.theme_tokens import (
    Breakpoint,
    Color,
    Elevation,
    Radius,
    Spacing,
    Typography,
)
from drishtix.ui.widgets.bento_grid import BentoGrid, BentoTile, ResponsiveBentoGrid
from drishtix.ui.widgets.empty_state import EmptyStateWidget
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.kpi_card import KPICard
from drishtix.ui.widgets.pill_badge import (
    CAPSULE_STATUS_MAP,
    PillBadge,
    PillStatus,
    StatusCapsule,
)
from drishtix.ui.widgets.section_header import SectionHeader

STYLES_DIR = Path(__file__).resolve().parents[1] / "drishtix" / "ui" / "styles"


@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication instance is initialized for GUI component testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_apply_class(qapp):
    """Test that apply_class properly sets property and executes polish cycle."""
    w = QWidget()
    apply_class(w, "glass-card")
    assert w.property("class") == "glass-card"

    apply_class(w, "neu-raised")
    assert w.property("class") == "neu-raised"


def test_pill_badge_status_mapping(qapp):
    """Test PillBadge initialization and runtime status changes."""
    badge = PillBadge("LIVE", PillStatus.LIVE)
    assert badge.property("class") == "pill-live"
    assert badge.text() == "LIVE"

    badge.set_status(PillStatus.CRITICAL)
    assert badge.property("class") == "pill-critical"

    badge.set_text("ALERT")
    assert badge.text() == "ALERT"


def test_status_capsule(qapp):
    """Test StatusCapsule runtime status updates and monospace variants."""
    cap = StatusCapsule("FPS: 30", status="safe", monospace=True)
    assert cap.property("class") == "status-capsule-safe"
    # Monospace is orthogonal to status, so switching status must not
    # disturb it — the FPS capsule re-applies its class on every frame.
    assert cap.property("mono") is True

    cap.set_capsule_status("critical")
    assert cap.property("class") == "status-capsule-critical"
    assert cap.property("mono") is True

    plain = StatusCapsule("RAM: 142 MB", status="neutral")
    assert plain.property("class") == "status-capsule-neutral"
    assert plain.property("mono") is False


def test_every_capsule_status_has_a_qss_rule():
    """
    Every class StatusCapsule can emit must exist in the generated QSS.

    A capsule whose class matches no rule renders completely unstyled — no
    background, border, padding or colour. That is exactly what happened
    when monospace was a "-mono" class suffix: only the neutral twin was
    ever written, so the mono FPS capsule lost all styling the instant
    _on_fps_updated moved it off "neutral".
    """
    qss = (STYLES_DIR / "drishtix_glass.qss").read_text(encoding="utf-8")

    for status, class_name in CAPSULE_STATUS_MAP.items():
        assert f'[class="{class_name}"]' in qss, (
            f'status "{status}" maps to "{class_name}", which has no QSS rule'
        )

    # The monospace variant is applied as a property, not a class suffix.
    assert '[mono="true"]' in qss, "monospace capsule variant has no QSS rule"


def test_glass_card_variants(qapp):
    """Test GlassCard initialization with different CardVariants and shadow effect."""
    for variant in CardVariant:
        card = GlassCard(variant=variant)
        assert card.property("class") == variant.value
        assert card.graphicsEffect() is not None


def test_bento_grid_structure(qapp):
    """Test BentoGrid column configuration and widget placement."""
    grid = BentoGrid(columns=12, gap=14)
    assert grid.columns == 12

    w1 = QLabel("Video")
    w2 = QLabel("Sidebar")
    grid.add_tile(w1, col=0, col_span=8, row=0, row_span=2)
    grid.add_tile(w2, col=8, col_span=4, row=0, row_span=2)

    assert grid.grid_layout().count() == 2


def test_responsive_bento_grid(qapp):
    """Test ResponsiveBentoGrid column reflow methods."""
    grid = ResponsiveBentoGrid(columns=12)
    assert grid.columns == 12

    grid.set_columns(1)
    assert grid.columns == 1

    grid.set_columns(6)
    assert grid.columns == 6


def test_kpi_card_values(qapp):
    """Test KPICard label assignment and accessibility info."""
    kpi = KPICard("Total Targets", "100")
    assert kpi.property("class") == "kpi-card"
    assert kpi.lbl_title.text() == "TOTAL TARGETS"
    assert kpi.lbl_val.text() == "100"

    kpi.set_value("250", "#10B981")
    assert kpi.lbl_val.text() == "250"


def test_empty_state_widget(qapp):
    """Test EmptyStateWidget configuration."""
    empty = EmptyStateWidget(icon="🛡️", message="Secure", action_text="Configure")
    assert empty.property("class") == "empty-state"
    assert empty._lbl_icon.text() == "🛡️"
    assert empty._lbl_message.text() == "Secure"
    assert empty._btn_action.text() == "Configure"


def test_empty_state_widget_without_action(qapp):
    """
    The action button must exist even with no action text.

    It used to be created only inside `if action_text:`, so every attribute
    access on an action-less empty state raised AttributeError.
    """
    empty = EmptyStateWidget(icon="📭", message="Nothing here")
    assert empty._btn_action is not None
    assert empty._btn_action.isHidden()          # hidden, not absent

    empty.set_action("Retry")
    assert empty._btn_action.text() == "Retry"
    assert not empty._btn_action.isHidden()


def test_section_header_optional_subtitle(qapp):
    """The subtitle label must exist (hidden) even when no subtitle is given."""
    header = SectionHeader("REGISTRY")
    assert header._lbl_title.text() == "REGISTRY"
    assert header._lbl_subtitle is not None
    assert header._lbl_subtitle.isHidden()

    header.set_subtitle("Manage watchlist targets")
    assert header._lbl_subtitle.text() == "Manage watchlist targets"
    assert not header._lbl_subtitle.isHidden()

    header.add_action(PillBadge("0 TARGETS", PillStatus.NEUTRAL))
    assert header._action_layout.count() == 1


def test_apply_status(qapp):
    """apply_status must set the `status` property used by QSS state selectors."""
    w = QWidget()
    apply_status(w, "safe")
    assert w.property("status") == "safe"

    apply_status(w, "critical")
    assert w.property("status") == "critical"


def test_bento_tile_carries_its_own_span(qapp):
    """
    add_bento_tile() must honour the span stored on the tile.

    add_tile() ignores BentoTile.col_span/row_span, which silently collapsed
    tiles to 1x1 when callers relied on the tile to carry its own geometry.
    """
    tile = BentoTile(QLabel("Video"), col_span=8, row_span=2)
    assert isinstance(tile, QFrame)
    assert tile.property("class") == "bento-tile"

    grid = BentoGrid(columns=12)
    grid.add_bento_tile(tile, col=0, row=0)

    layout = grid.grid_layout()
    assert layout.count() == 1
    row, col, row_span, col_span = layout.getItemPosition(0)
    assert (row, col, row_span, col_span) == (0, 0, 2, 8)


def test_theme_token_integrity():
    """Design tokens must be well-formed — QSS silently drops malformed values."""
    hex_tokens = [Color.TEXT_PRIMARY, Color.CANVAS, Color.ACCENT, Color.WHITE]
    for token in hex_tokens:
        assert token.startswith("#") and len(token) == 7, token

    # Radii and spacing feed directly into px values
    for value in (Radius.TILE, Radius.CARD, Radius.CONTROL, Spacing.BENTO_GAP):
        assert isinstance(value, int) and value >= 0

    # Breakpoints must be strictly ordered or reflow thresholds overlap
    assert Breakpoint.COMPACT < Breakpoint.WIDE

    # Elevation tiers must increase monotonically
    tiers = [Elevation.RESTING, Elevation.HOVER, Elevation.OVERLAY]
    assert [t.blur for t in tiers] == sorted(t.blur for t in tiers)
    assert [t.alpha for t in tiers] == sorted(t.alpha for t in tiers)

    assert "Inter" in Typography.SANS
    assert "Consolas" in Typography.MONO or "Mono" in Typography.MONO


def test_qss_template_renders_and_matches_tokens():
    """
    The QSS template must render against the current tokens, and the
    checked-in .qss must reflect them.

    drishtix_glass.qss is generated output (tools/generate_qss.py); renaming a
    token without regenerating leaves the app styled from a stale file.
    """
    jinja2 = pytest.importorskip("jinja2")

    template_file = STYLES_DIR / "drishtix_glass.qss.j2"
    output_file = STYLES_DIR / "drishtix_glass.qss"
    assert template_file.exists(), f"missing template: {template_file}"
    assert output_file.exists(), f"missing generated QSS: {output_file}"

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STYLES_DIR)),
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    rendered = env.get_template(template_file.name).render(
        color=Color,
        elevation=Elevation,
        radius=Radius,
        spacing=Spacing,
        breakpoint=Breakpoint,
        typography=Typography,
    )
    assert rendered.strip(), "template rendered empty"

    existing = output_file.read_text(encoding="utf-8")
    for token in (Color.ACCENT, Color.CANVAS, Color.TEXT_PRIMARY):
        assert token in existing, f"{token} missing from generated QSS — regenerate it"


def test_sparkline_widget(qapp):
    """Test Sparkline widget data initialization and updates."""
    from drishtix.ui.widgets.sparkline import Sparkline

    spark = Sparkline([10.0, 20.0, 15.0, 30.0])
    assert spark.height() == 28
    spark.set_data([5.0, 10.0, 25.0])
    assert spark._data == [5.0, 10.0, 25.0]


def test_circular_progress_widget(qapp):
    """Test CircularProgress ring widget value clamp and configuration."""
    from drishtix.ui.widgets.circular_progress import CircularProgress

    ring = CircularProgress(value=75.0, max_value=100.0, size=36)
    assert ring.width() == 36
    assert ring._value == 75.0

    ring.set_value(120.0)  # Clamps to max_value 100.0
    assert ring._value == 100.0


def test_activity_heatmap_widget(qapp):
    """Test ActivityHeatmap 24-hour strip data handling."""
    from drishtix.ui.widgets.activity_heatmap import ActivityHeatmap

    heatmap = ActivityHeatmap()
    assert len(heatmap._counts) == 24

    heatmap.set_data([{"hour": 8, "count": 15}, {"hour": 18, "count": 42}])
    assert heatmap._counts[8] == 15
    assert heatmap._counts[18] == 42


def test_confidence_bar_widget(qapp):
    """Test ConfidenceBar percentage progress indicator."""
    from drishtix.ui.widgets.confidence_bar import ConfidenceBar

    bar = ConfidenceBar(confidence=0.88)
    assert bar._confidence == 0.88
    assert bar.height() == 24

    bar.set_confidence(0.45)
    assert bar._confidence == 0.45


def test_system_health_card_widget(qapp):
    """Test SystemHealthCard live telemetry monitoring container."""
    from drishtix.ui.widgets.system_health_card import SystemHealthCard

    card = SystemHealthCard()
    assert card.lbl_fps_val is not None
    assert card.lbl_ram_val is not None
    assert card.lbl_cpu_val is not None
    assert card.lbl_uptime_val is not None


def test_timeline_strip_widget(qapp):
    """Test TimelineStrip chronological incident timeline."""
    from datetime import datetime
    from drishtix.ui.widgets.timeline_strip import TimelineStrip

    events = [
        {"timestamp": datetime.now(), "full_name": "Target A", "category": "CRIMINAL", "confidence": 0.92}
    ]
    strip = TimelineStrip(events=events, hours_window=4)
    assert strip.height() == 38
    assert len(strip._events) == 1

