"""UI views package."""

from drishtix.ui.views.dashboard_view import DashboardView
from drishtix.ui.views.registry_view import RegistryView
from drishtix.ui.views.detection_log_view import DetectionLogView
from drishtix.ui.views.analytics_view import AnalyticsView
from drishtix.ui.views.image_scan_view import ImageScanView
from drishtix.ui.views.settings_view import SettingsView

__all__ = [
    "DashboardView",
    "RegistryView",
    "DetectionLogView",
    "AnalyticsView",
    "ImageScanView",
    "SettingsView",
]
