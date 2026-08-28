"""Integration tests for analytics aggregation queries."""

from datetime import datetime
import pytest

from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.session import get_session, initialize, shutdown
from drishtix.dao.target_dao import TargetDAO
from drishtix.models.detection_log import DetectionLog
from drishtix.models.target_registry import TargetRegistry
from drishtix.services.analytics_service import DetectionAnalyticsService


@pytest.fixture(autouse=True)
def setup_analytics_db(tmp_path):
    db_file = tmp_path / "test_analytics.db"
    initialize(str(db_file))

    with get_session() as session:
        # Create targets
        t1 = TargetRegistry(full_name="Target Alpha", category="CRIMINAL", is_active=True)
        t2 = TargetRegistry(full_name="Target Beta", category="MISSING_PERSON", is_active=True)
        TargetDAO.create(session, t1)
        TargetDAO.create(session, t2)

        # Log detections
        DetectionLogDAO.create(session, DetectionLog(target_id=t1.target_id, match_confidence=0.92, location_tag="Cam A"))
        DetectionLogDAO.create(session, DetectionLog(target_id=t1.target_id, match_confidence=0.88, location_tag="Cam A"))
        DetectionLogDAO.create(session, DetectionLog(target_id=t2.target_id, match_confidence=0.95, location_tag="Cam B"))

    yield
    shutdown()


def test_analytics_kpis():
    kpis = DetectionAnalyticsService.get_kpis()
    assert kpis.total_detections == 3
    assert kpis.unique_targets == 2
    assert kpis.avg_confidence > 0.85
    assert kpis.active_targets == 2


def test_category_breakdown():
    breakdown = DetectionAnalyticsService.get_category_breakdown()
    counts = {b["category"]: b["count"] for b in breakdown}
    assert counts.get("CRIMINAL") == 2
    assert counts.get("MISSING_PERSON") == 1


def test_top_targets():
    top = DetectionAnalyticsService.get_top_targets(limit=5)
    assert len(top) == 2
    assert top[0]["full_name"] == "Target Alpha"
    assert top[0]["count"] == 2
