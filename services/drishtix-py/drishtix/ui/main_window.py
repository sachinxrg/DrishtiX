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

from drishtix.core.constants import APP_NAME, APP_VERSION, NAV_SIDEBAR_WIDTH
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
        """Create navigation sidebar."""
        sidebar = QFrame()
        sidebar.setObjectName("NavSidebar")
        sidebar.setFixedWidth(NAV_SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # Logo & App Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl_logo = QLabel("👁️")
        lbl_logo.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(lbl_logo)

        lbl_title = QLabel("DRISHTIX")
        lbl_title.setStyleSheet("font-weight: 800; font-size: 16px; letter-spacing: 1.5px; color: #E8EAED;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        lbl_subtitle = QLabel("TACTICAL PERIMETER AI")
        lbl_subtitle.setStyleSheet("color: #555A65; font-size: 9px; font-weight: bold; margin-bottom: 16px; margin-left: 2px;")
        layout.addWidget(lbl_subtitle)

        # Nav Items
        nav_items = [
            ("Dashboard", 0),
            ("Target Registry", 1),
            ("Detection Logs", 2),
            ("Analytics & KPIs", 3),
            ("Forensic Image Scan", 4),
            ("Settings & Config", 5),
        ]

        for text, index in nav_items:
            btn = NavButton(text, index, sidebar)
            btn.clicked.connect(lambda _, idx=index: self._select_view(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Footer Version Info
        lbl_ver = QLabel(f"DrishtiX Edge {APP_VERSION}")
        lbl_ver.setStyleSheet("color: #444855; font-size: 10px;")
        layout.addWidget(lbl_ver)

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
