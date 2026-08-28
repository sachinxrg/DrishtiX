"""
DrishtiX v4.0 — DetectionLog DAO.

Migrated from: com.drishtix.dao.DetectionLogDAO (Java)
Handles CRUD and aggregation queries for detection events.
The aggregation pipelines from MongoDB are replaced with SQLAlchemy
query builder expressions over SQLite.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func as sql_func, desc, and_, extract
from sqlalchemy.orm import Session, joinedload

from drishtix.models.detection_log import DetectionLog
from drishtix.models.target_registry import TargetRegistry

logger = logging.getLogger(__name__)


class DetectionLogDAO:
    """Repository for DetectionLog CRUD and analytics aggregation queries."""

    @staticmethod
    def create(session: Session, log: DetectionLog) -> DetectionLog:
        """Insert a new detection log entry."""
        session.add(log)
        session.flush()
        logger.debug(
            "Detection logged: id=%d, target_id=%d, confidence=%.3f",
            log.log_id, log.target_id, log.match_confidence,
        )
        return log

    @staticmethod
    def get_recent(
        session: Session,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
        target_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[DetectionLog]:
        """
        Retrieve recent detection logs with optional filtering.

        Supports pagination and filtering by category, target name, and date range.
        Results are returned with eagerly loaded target and camera relationships.
        """
        stmt = (
            select(DetectionLog)
            .join(TargetRegistry)
            .options(
                joinedload(DetectionLog.target),
                joinedload(DetectionLog.camera),
            )
            .order_by(desc(DetectionLog.detection_timestamp))
        )

        if category:
            stmt = stmt.where(TargetRegistry.category == category)
        if target_name:
            stmt = stmt.where(TargetRegistry.full_name.ilike(f"%{target_name}%"))
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)

        stmt = stmt.offset(offset).limit(limit)
        return list(session.execute(stmt).unique().scalars().all())

    @staticmethod
    def count_total(
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count total detections, optionally within a date range."""
        stmt = select(sql_func.count()).select_from(DetectionLog)
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)
        return session.execute(stmt).scalar_one()

    @staticmethod
    def count_unique_targets(
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count distinct targets detected within a date range."""
        stmt = select(sql_func.count(sql_func.distinct(DetectionLog.target_id)))
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)
        return session.execute(stmt).scalar_one()

    @staticmethod
    def avg_confidence(
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Calculate average match confidence within a date range."""
        stmt = select(sql_func.avg(DetectionLog.match_confidence))
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)
        result = session.execute(stmt).scalar_one()
        return result if result is not None else 0.0

    @staticmethod
    def hourly_distribution(session: Session, date: Optional[datetime] = None) -> list[dict]:
        """
        Get hourly detection count distribution for a specific date.

        Returns a list of 24 dicts: [{'hour': 0, 'count': 5}, ...]
        Replaces the legacy MongoDB $group + $dateToString aggregation.
        """
        if date is None:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        # SQLite strftime for hour extraction
        hour_col = sql_func.cast(
            sql_func.strftime("%H", DetectionLog.detection_timestamp), type_=type(0)
        )

        stmt = (
            select(
                sql_func.strftime("%H", DetectionLog.detection_timestamp).label("hour"),
                sql_func.count().label("count"),
            )
            .where(
                and_(
                    DetectionLog.detection_timestamp >= start,
                    DetectionLog.detection_timestamp < end,
                )
            )
            .group_by("hour")
            .order_by("hour")
        )

        rows = session.execute(stmt).all()
        hour_map = {int(r.hour): r.count for r in rows}

        return [{"hour": h, "count": hour_map.get(h, 0)} for h in range(24)]

    @staticmethod
    def daily_trend(session: Session, days: int = 7) -> list[dict]:
        """
        Get daily detection counts for the last N days.

        Returns a list of dicts: [{'date': '2026-08-23', 'count': 42}, ...]
        """
        start = datetime.now() - timedelta(days=days)

        stmt = (
            select(
                sql_func.date(DetectionLog.detection_timestamp).label("date"),
                sql_func.count().label("count"),
            )
            .where(DetectionLog.detection_timestamp >= start)
            .group_by("date")
            .order_by("date")
        )

        rows = session.execute(stmt).all()
        return [{"date": str(r.date), "count": r.count} for r in rows]

    @staticmethod
    def category_breakdown(
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Get detection counts grouped by target category.

        Returns: [{'category': 'CRIMINAL', 'count': 120}, ...]
        """
        stmt = (
            select(
                TargetRegistry.category,
                sql_func.count(DetectionLog.log_id).label("count"),
            )
            .select_from(DetectionLog)
            .join(TargetRegistry, DetectionLog.target_id == TargetRegistry.target_id)
        )
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)

        stmt = stmt.group_by(TargetRegistry.category)
        rows = session.execute(stmt).all()
        return [{"category": r.category, "count": r.count} for r in rows]

    @staticmethod
    def top_detected_targets(
        session: Session,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Get the top N most frequently detected targets.

        Returns: [{'target_id': 1, 'full_name': 'John', 'category': 'CRIMINAL', 'count': 42}, ...]
        """
        stmt = (
            select(
                TargetRegistry.target_id,
                TargetRegistry.full_name,
                TargetRegistry.category,
                sql_func.count(DetectionLog.log_id).label("count"),
            )
            .select_from(DetectionLog)
            .join(TargetRegistry, DetectionLog.target_id == TargetRegistry.target_id)
        )
        if start_date:
            stmt = stmt.where(DetectionLog.detection_timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DetectionLog.detection_timestamp <= end_date)

        stmt = (
            stmt.group_by(TargetRegistry.target_id, TargetRegistry.full_name, TargetRegistry.category)
            .order_by(desc("count"))
            .limit(limit)
        )

        rows = session.execute(stmt).all()
        return [
            {
                "target_id": r.target_id,
                "full_name": r.full_name,
                "category": r.category,
                "count": r.count,
            }
            for r in rows
        ]
