"""
DrishtiX v4.0 — Tactical Command MainWindow.

Bento Grid main window architecture featuring a collapsible navigation sidebar,
stacked view container, and real-time diagnostic status bar.
Migrated from: com.drishtix.controller.MainController (Java)
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
from drishtix.ui.views.analytics_view import AnalyticsView
from drishtix.ui.views.dashboard_view import DashboardView
from drishtix.ui.views.detection_log_view import DetectionLogView
from drishtix.ui.views.image_scan_view import ImageScanView
from drishtix.ui.views.registry_view import RegistryView
from drishtix.ui.views.settings_view import SettingsView
from drishtix.ui.widgets.nav_button import NavButton
from drishtix.ui.widgets.status_bar import StatusBar
from drishtix.workers.capture_worker import CaptureWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary Tactical Command Window for DrishtiX v4.0."""

    def __init__(self, capture_worker: Optional[CaptureWorker] = None) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Edge AI Perimeter Intelligence")
        self.resize(1360, 850)
        self.setMinimumSize(1024, 680)

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

        # 1. Left Command Sidebar (Fixed 220px)
        sidebar = self._create_sidebar()
        workspace.addWidget(sidebar)

        # Set Window Icon from assets if available
        logo_path = ASSETS_DIR / "drishtix_logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        # 2. Central QStackedWidget
        self.content_stack = QStackedWidget()

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

        workspace.addWidget(self.content_stack, stretch=1)
        root_vbox.addLayout(workspace, stretch=1)

        # ─── 3. Bottom Status Bar (Fixed 32px) ───────────────────────
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
        layout.setSpacing(8)

        # Logo & App Title Container
        brand_card = QFrame()
        brand_card.setStyleSheet("background: transparent; border: none; margin-bottom: 8px;")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Official Logo Image
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(36, 36)
        logo_path = ASSETS_DIR / "drishtix_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path)).scaled(
                36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pm)
        else:
            self.lbl_logo.setText("👁️")
            self.lbl_logo.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(self.lbl_logo)

        # Title & Badge
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)
        title_vbox.setContentsMargins(0, 0, 0, 0)

        lbl_title = QLabel("DRISHTIX")
        lbl_title.setStyleSheet("font-weight: 900; font-size: 16px; letter-spacing: 1.8px; color: #0F172A;")
        title_vbox.addWidget(lbl_title)

        lbl_subtitle = QLabel("TACTICAL EDGE AI")
        lbl_subtitle.setStyleSheet("color: #4F6BFB; font-size: 9px; font-weight: 800; letter-spacing: 1px;")
        title_vbox.addWidget(lbl_subtitle)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        brand_layout.addLayout(header_layout)

        # Divider line
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #E2E8F0; margin-top: 4px; margin-bottom: 8px;")
        brand_layout.addWidget(div)

        layout.addWidget(brand_card)

        # Nav Items with refined icons & labels
        nav_items = [
            ("📊  Dashboard", 0),
            ("🎯  Target Registry", 1),
            ("📜  Detection Logs", 2),
            ("📈  Analytics & KPIs", 3),
            ("🔍  Forensic Scanner", 4),
            ("⚙️  Settings & Config", 5),
        ]

        for text, index in nav_items:
            btn = NavButton(text, index, sidebar)
            btn.clicked.connect(lambda _, idx=index: self._select_view(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Footer Version Info Card
        ver_card = QFrame()
        ver_card.setStyleSheet("background-color: #F1F5F9; border-radius: 10px; padding: 6px 10px; border: 1px solid #E2E8F0;")
        ver_layout = QHBoxLayout(ver_card)
        ver_layout.setContentsMargins(6, 4, 6, 4)
        ver_layout.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet("color: #10B981; font-size: 10px;")
        ver_layout.addWidget(dot)

        lbl_ver = QLabel(f"DrishtiX {APP_VERSION}")
        lbl_ver.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600;")
        ver_layout.addWidget(lbl_ver)
        ver_layout.addStretch()

        layout.addWidget(ver_card)

        return sidebar

    def _select_view(self, index: int) -> None:
        """Switch active view in QStackedWidget and update button highlight."""
        self.content_stack.setCurrentIndex(index)

        for btn in self._nav_buttons:
            btn.setChecked(btn.index == index)

        # Refresh data when switching to specific views
        if index == 1:
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
