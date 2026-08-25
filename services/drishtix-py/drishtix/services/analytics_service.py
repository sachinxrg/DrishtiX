"""
DrishtiX v4.0 — Detection Analytics Service.

Provides aggregated reporting data and KPI metrics for the Analytics Dashboard.
Migrated from: com.drishtix.service.DetectionAnalyticsService (Java)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from drishtix.dao.camera_dao import CameraDAO
from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.session import get_session
from drishtix.dao.target_dao import TargetDAO

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsKPIs:
    """High-level KPI metrics summary."""

    total_detections: int
    unique_targets: int
    avg_confidence: float
    active_targets: int
    active_cameras: int


class DetectionAnalyticsService:
    """
    Analytics service aggregating SQLite logs for chart generation and KPI cards.
    """

    @staticmethod
    def get_kpis(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnalyticsKPIs:
        """Fetch primary KPIs for the selected date range."""
        with get_session() as session:
            total = DetectionLogDAO.count_total(session, start_date, end_date)
            unique = DetectionLogDAO.count_unique_targets(session, start_date, end_date)
            avg_conf = DetectionLogDAO.avg_confidence(session, start_date, end_date)
            active_targets = TargetDAO.count_active(session)
            active_cams = len(CameraDAO.get_all(session, active_only=True))

            return AnalyticsKPIs(
                total_detections=total,
                unique_targets=unique,
                avg_confidence=avg_conf,
                active_targets=active_targets,
                active_cameras=max(1, active_cams),
            )

    @staticmethod
    def get_hourly_distribution(date: Optional[datetime] = None) -> List[Dict[str, int]]:
        """Fetch 24-hour distribution counts."""
        with get_session() as session:
            return DetectionLogDAO.hourly_distribution(session, date)

    @staticmethod
    def get_daily_trend(days: int = 7) -> List[Dict[str, object]]:
        """Fetch daily trend for the past N days."""
        with get_session() as session:
            return DetectionLogDAO.daily_trend(session, days)

    @staticmethod
    def get_category_breakdown(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, object]]:
        """Fetch detection volume grouped by target category."""
        with get_session() as session:
            return DetectionLogDAO.category_breakdown(session, start_date, end_date)

    @staticmethod
    def get_top_targets(
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, object]]:
        """Fetch top detected targets list."""
        with get_session() as session:
            return DetectionLogDAO.top_detected_targets(session, limit, start_date, end_date)
