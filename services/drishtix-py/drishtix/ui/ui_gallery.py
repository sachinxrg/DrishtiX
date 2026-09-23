"""
DrishtiX v5.0 — UI Component Gallery Dev Harness.

Standalone QMainWindow script that instantiates every DS widget in every variant/state
on a scrollable canvas.
Used for:
  1. Fast interactive design iteration without booting camera / AI stack.
  2. Visual regression testing baseline fixture.

Usage:
    python -m drishtix.ui.ui_gallery
    python drishtix/ui/ui_gallery.py
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.widgets.activity_heatmap import ActivityHeatmap
from drishtix.ui.widgets.ambient_background import AmbientBackground
from drishtix.ui.widgets.circular_progress import CircularProgress
from drishtix.ui.widgets.confidence_bar import ConfidenceBar
from drishtix.ui.widgets.empty_state import EmptyStateWidget
from drishtix.ui.widgets.glass_card import CardVariant, GlassCard
from drishtix.ui.widgets.kpi_card import KPICard
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus, StatusCapsule
from drishtix.ui.widgets.section_header import SectionHeader
from drishtix.ui.widgets.sparkline import Sparkline
from drishtix.ui.widgets.system_health_card import SystemHealthCard


class UIGalleryWindow(QMainWindow):
    """Component catalog window for Design System visual inspection."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DrishtiX v5.0 — Design System Component Gallery")
        self.resize(1260, 920)
        self.setMinimumSize(960, 640)

        self._init_ui()

    def _init_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        container = AmbientBackground()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── 1. Section Header ─────────────────────────────────────────
        gallery_header = SectionHeader(
            "DRISHTIX v5.0 DESIGN SYSTEM GALLERY",
            "Interactive showcase of all light-theme design tokens, glass/neu variants, and custom widgets",
            icon="🎨",
        )
        btn_refresh = QPushButton("Refresh QSS")
        apply_class(btn_refresh, "btn-primary")
        btn_refresh.clicked.connect(self._reload_qss)
        gallery_header.add_action(btn_refresh)
        layout.addWidget(gallery_header)

        # ── 2. Top Bento KPI Cards with Micro Visuals ─────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        kpi1 = KPICard("Total Detections", "14,892", icon="📊", accent_color=Color.ACCENT)
        kpi1.set_sparkline_data([12.0, 18.0, 9.0, 24.0, 31.0, 19.0, 42.0])

        kpi2 = KPICard("Unique Targets", "42", icon="🎯", accent_color=Color.SAFE)

        kpi3 = KPICard("Avg Confidence", "97.4%", icon="⚡", accent_color=Color.WARNING)
        kpi3.set_progress_ring(97.4, 100.0, Color.WARNING)

        kpi4 = KPICard("Active Perimeter", "4 Nodes", icon="📹", accent_color=Color.INFO)

        kpi_row.addWidget(kpi1)
        kpi_row.addWidget(kpi2)
        kpi_row.addWidget(kpi3)
        kpi_row.addWidget(kpi4)
        layout.addLayout(kpi_row)

        # ── 3. Pill Badges & Status Capsules ─────────────────────────
        pills_card = GlassCard(variant=CardVariant.GLASS)
        pills_layout = pills_card.content_layout()
        pills_layout.addWidget(QLabel("<b>Pill Badges (Semantic Status)</b>"))

        pills_row = QHBoxLayout()
        pills_row.addWidget(PillBadge("● LIVE FEED", PillStatus.LIVE))
        pills_row.addWidget(PillBadge("● OFFLINE", PillStatus.OFFLINE))
        pills_row.addWidget(PillBadge("SAFE", PillStatus.SAFE))
        pills_row.addWidget(PillBadge("REVIEW", PillStatus.WARNING))
        pills_row.addWidget(PillBadge("CRITICAL", PillStatus.CRITICAL))
        pills_row.addWidget(PillBadge("INFO", PillStatus.INFO))
        pills_row.addWidget(PillBadge("ACCENT", PillStatus.ACCENT))
        pills_row.addWidget(PillBadge("CAM 01 • 1080p", PillStatus.NEUTRAL))
        pills_row.addStretch()
        pills_layout.addLayout(pills_row)

        pills_layout.addWidget(QLabel("<b>Status Capsules (Telemetry / Diagnostics)</b>"))
        caps_row = QHBoxLayout()
        caps_row.addWidget(StatusCapsule("● SYSTEM READY", "safe"))
        caps_row.addWidget(StatusCapsule("CAM: ONLINE", "safe"))
        caps_row.addWidget(StatusCapsule("FPS: 30.0", "safe", monospace=True))
        caps_row.addWidget(StatusCapsule("FPS: 12.4", "warning", monospace=True))
        caps_row.addWidget(StatusCapsule("CAM: OFFLINE", "critical"))
        caps_row.addWidget(StatusCapsule("DB: CONNECTED", "safe"))
        caps_row.addWidget(StatusCapsule("TARGETS: 128", "accent"))
        caps_row.addWidget(StatusCapsule("RAM: 142 MB", "neutral", monospace=True))
        caps_row.addStretch()
        pills_layout.addLayout(caps_row)

        layout.addWidget(pills_card)

        # ── 4. 24h Activity Heatmap & Confidence Bars ─────────────────
        heat_card = GlassCard(variant=CardVariant.GLASS)
        heat_layout = heat_card.content_layout()
        heat_layout.addWidget(QLabel("<b>24-Hour Surveillance Activity Heatmap</b>"))

        sample_hourly = [{"hour": h, "count": (h * 7) % 25 if h in (8, 9, 10, 14, 15, 18, 19, 20) else 0} for h in range(24)]
        heatmap = ActivityHeatmap(hourly_data=sample_hourly)
        heat_layout.addWidget(heatmap)

        heat_layout.addWidget(QLabel("<b>Confidence Progress Bars</b>"))
        conf_row = QHBoxLayout()
        conf_row.addWidget(ConfidenceBar(confidence=0.88))
        conf_row.addWidget(ConfidenceBar(confidence=0.62))
        conf_row.addWidget(ConfidenceBar(confidence=0.38))
        conf_row.addStretch()
        heat_layout.addLayout(conf_row)

        layout.addWidget(heat_card)

        # ── 5. System Health Card ────────────────────────────────────
        health = SystemHealthCard()
        layout.addWidget(health)

        # ── 6. Card Variants Matrix ──────────────────────────────────
        cards_grid = QGridLayout()
        cards_grid.setSpacing(14)

        card_glass = GlassCard(variant=CardVariant.GLASS)
        c_layout1 = card_glass.content_layout()
        c_layout1.addWidget(QLabel("<b>CardVariant.GLASS</b>"))
        c_layout1.addWidget(QLabel("0.78 opacity white fill + hairline border + resting elevation"))
        cards_grid.addWidget(card_glass, 0, 0)

        card_heavy = GlassCard(variant=CardVariant.GLASS_HEAVY)
        c_layout2 = card_heavy.content_layout()
        c_layout2.addWidget(QLabel("<b>CardVariant.GLASS_HEAVY</b>"))
        c_layout2.addWidget(QLabel("Heavy 0.88 opacity glass for high-density modal surfaces"))
        cards_grid.addWidget(card_heavy, 0, 1)

        card_elevated = GlassCard(variant=CardVariant.ELEVATED)
        c_layout3 = card_elevated.content_layout()
        c_layout3.addWidget(QLabel("<b>CardVariant.ELEVATED</b>"))
        c_layout3.addWidget(QLabel("0.82 opacity surface with prominent elevation for hero cards"))
        cards_grid.addWidget(card_elevated, 1, 0)

        card_neu = GlassCard(variant=CardVariant.NEU_RAISED)
        c_layout4 = card_neu.content_layout()
        c_layout4.addWidget(QLabel("<b>CardVariant.NEU_RAISED</b>"))
        c_layout4.addWidget(QLabel("Dual light/dark shadow edges for soft physical depth"))
        cards_grid.addWidget(card_neu, 1, 1)

        layout.addLayout(cards_grid)

        # ── 7. Empty State Demo ──────────────────────────────────────
        empty_demo = EmptyStateWidget(
            icon="🛡️",
            message="Perimeter Secure\nNo active target detections in the last 24 hours.",
            action_text="Open Settings",
            action_callback=lambda: None,
        )
        layout.addWidget(empty_demo)

    def _reload_qss(self) -> None:
        """Dynamically reload QSS at runtime."""
        qss_path = PROJECT_ROOT / "drishtix" / "ui" / "styles" / "drishtix_glass.qss"
        if qss_path.exists():
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
                print("QSS reloaded dynamically.")


def main() -> None:
    app = QApplication(sys.argv)
    qss_path = PROJECT_ROOT / "drishtix" / "ui" / "styles" / "drishtix_glass.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    win = UIGalleryWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
