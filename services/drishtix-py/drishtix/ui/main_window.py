"""
DrishtiX v5.0 — Tactical Command MainWindow.

Bento Grid main window architecture featuring a navigation command sidebar,
stacked view container with ambient gradient mesh background, and real-time
telemetry status bar.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from drishtix.core.constants import APP_NAME, APP_VERSION, ASSETS_DIR, NAV_SIDEBAR_WIDTH
from drishtix.core.feature_flags import ENABLE_BENTO_UI
from drishtix.ui.icons import render_svg_pixmap
from drishtix.ui.motion import FadingStackedWidget, PulsingStatusDot, SlidingIndicatorPill
from drishtix.ui.style_utils import apply_class
from drishtix.ui.theme_tokens import Color, Spacing
from drishtix.ui.views.analytics_view import AnalyticsView
from drishtix.ui.views.dashboard_view import DashboardView
from drishtix.ui.views.detection_log_view import DetectionLogView
from drishtix.ui.views.image_scan_view import ImageScanView
from drishtix.ui.views.registry_view import RegistryView
from drishtix.ui.views.settings_view import SettingsView
from drishtix.ui.widgets.ambient_background import AmbientBackground
from drishtix.ui.widgets.nav_button import NavButton
from drishtix.ui.widgets.pill_badge import PillBadge, PillStatus
from drishtix.ui.widgets.status_bar import StatusBar
from drishtix.workers.capture_worker import CaptureWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary Tactical Command Window for DrishtiX v5.0."""

    def __init__(self, capture_worker: Optional[CaptureWorker] = None) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Edge AI Perimeter Intelligence")
        self.resize(1380, 880)
        self.setMinimumSize(1080, 700)

        self.capture_worker = capture_worker
        self._nav_buttons: List[NavButton] = []

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_vbox = QVBoxLayout(central_widget)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        # ─── Main Workspace (Sidebar + Content Stack) ────────────────
        workspace = QHBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(0)

        # 1. Left Command Sidebar (Fixed 240px)
        sidebar = self._create_sidebar()
        workspace.addWidget(sidebar)

        # Set Window Icon from assets if available
        logo_path = ASSETS_DIR / "drishtix_logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        # 2. Content area with ambient gradient mesh
        if ENABLE_BENTO_UI:
            content_area: QWidget = AmbientBackground()
            self._ambient_bg: Optional[AmbientBackground] = content_area
        else:
            content_area = QWidget()
            self._ambient_bg = None

        content_area_layout = QVBoxLayout(content_area)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(0)

        # Central FadingStackedWidget with 21st UI cross-fade transitions
        self.content_stack = FadingStackedWidget(duration_ms=220)

        # Instantiate 6 Views
        self.view_dashboard = DashboardView(capture_worker=self.capture_worker)
        self.view_registry = RegistryView()
        self.view_logs = DetectionLogView()
        self.view_analytics = AnalyticsView()
        self.view_image_scan = ImageScanView()
        self.view_settings = SettingsView()

        self.content_stack.addWidget(self.view_dashboard)   # 0
        self.content_stack.addWidget(self.view_registry)    # 1
        self.content_stack.addWidget(self.view_logs)        # 2
        self.content_stack.addWidget(self.view_analytics)   # 3
        self.content_stack.addWidget(self.view_image_scan)  # 4
        self.content_stack.addWidget(self.view_settings)    # 5

        content_area_layout.addWidget(self.content_stack, stretch=1)

        workspace.addWidget(content_area, stretch=1)
        root_vbox.addLayout(workspace, stretch=1)

        # ─── 3. Bottom Status Bar (Fixed 36px) ───────────────────────
        self.status_bar = StatusBar()
        root_vbox.addWidget(self.status_bar)

        # Set default active view
        self._select_view(0)

    def _create_sidebar(self) -> QFrame:
        """Create navigation sidebar with official logo and polished navigation."""
        sidebar = QFrame()
        sidebar.setObjectName("NavSidebar")
        sidebar.setFixedWidth(NAV_SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        # ─── Brand Card Header ───────────────────────────────────────
        brand_card = QFrame()
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(0, 0, 0, 8)
        brand_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Official Logo Image
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(38, 38)
        logo_path = ASSETS_DIR / "drishtix_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path)).scaled(
                38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pm)
        else:
            self.lbl_logo.setPixmap(render_svg_pixmap("eye", Color.ACCENT, 28))
        header_layout.addWidget(self.lbl_logo)

        # Title & Subtitle
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)
        title_vbox.setContentsMargins(0, 0, 0, 0)

        lbl_title = QLabel("DRISHTIX")
        apply_class(lbl_title, "type-h2")
        lbl_title.setStyleSheet("font-weight: 800; letter-spacing: 0.5px;")
        title_vbox.addWidget(lbl_title)

        lbl_subtitle = QLabel("TACTICAL EDGE AI")
        apply_class(lbl_subtitle, "type-micro")
        lbl_subtitle.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-weight: 700; letter-spacing: 0.8px;")
        title_vbox.addWidget(lbl_subtitle)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        brand_layout.addLayout(header_layout)

        # Divider line
        div = QFrame()
        div.setFixedHeight(1)
        apply_class(div, "separator")
        brand_layout.addWidget(div)

        layout.addWidget(brand_card)

        # ─── Nav Items with 21st UI Vector Icons & Sliding Pill Indicator ──
        nav_container = QWidget(sidebar)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        self._nav_pill = SlidingIndicatorPill(parent=nav_container)

        nav_items = [
            ("Dashboard", 0, "dashboard"),
            ("Target Registry", 1, "target"),
            ("Detection Logs", 2, "logs"),
            ("Analytics & KPIs", 3, "analytics"),
            ("Forensic Scanner", 4, "scanner"),
            ("Settings & Config", 5, "settings"),
        ]

        for text, index, icon in nav_items:
            btn = NavButton(text, index, icon_text=icon, parent=nav_container)
            btn.clicked.connect(lambda _, idx=index: self._select_view(idx))
            self._nav_buttons.append(btn)
            nav_layout.addWidget(btn)

        layout.addWidget(nav_container)
        layout.addStretch()

        # ─── Footer Version Card with 21st UI Live Pulse ─────────────
        ver_frame = QFrame()
        apply_class(ver_frame, "neu-inset")
        ver_layout = QHBoxLayout(ver_frame)
        ver_layout.setContentsMargins(10, 8, 10, 8)
        ver_layout.setSpacing(8)

        ver_dot = PulsingStatusDot(color_hex=Color.SAFE, dot_radius=3.0, max_aura_radius=7.0, parent=ver_frame)
        ver_layout.addWidget(ver_dot)

        lbl_ver = QLabel(f"DrishtiX v{APP_VERSION}")
        apply_class(lbl_ver, "type-micro")
        lbl_ver.setStyleSheet(f"color: {Color.TEXT_SECONDARY}; font-weight: 600;")
        ver_layout.addWidget(lbl_ver)
        ver_layout.addStretch()

        layout.addWidget(ver_frame)

        return sidebar

    def _update_nav_indicator(self, animate: bool = True) -> None:
        """Align 21st UI sliding indicator pill with the active navigation button."""
        idx = self.content_stack.currentIndex()
        if 0 <= idx < len(self._nav_buttons):
            target_btn = self._nav_buttons[idx]
            if hasattr(self, "_nav_pill"):
                self._nav_pill.glide_to(target_btn, animate=animate)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_nav_indicator(animate=False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_nav_indicator(animate=False)

    def _select_view(self, index: int) -> None:
        """Switch active view in QStackedWidget and update button highlight."""
        self.content_stack.setCurrentIndex(index)

        for btn in self._nav_buttons:
            btn.setChecked(btn.index == index)

        self._update_nav_indicator(animate=True)

        # Refresh data when switching to specific views
        if index == 0:
            self.view_dashboard.refresh_metrics()
        elif index == 1:
            self.view_registry.load_targets()
        elif index == 2:
            self.view_logs.load_logs()
        elif index == 3:
            self.view_analytics.refresh_dashboard()

    def closeEvent(self, event) -> None:
        """Handle application close cleanup."""
        logger.info("MainWindow closing, stopping capture worker...")
        if self.capture_worker is not None and self.capture_worker.is_running():
            self.capture_worker.stop()
            self.capture_worker.wait(1000)
        event.accept()
