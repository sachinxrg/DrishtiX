"""
DrishtiX v4.0 — Data Export Service.

Exports detection logs and registry tables to CSV format.
Migrated from: com.drishtix.service.ExportService (Java)
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.session import get_session
from drishtix.dao.target_dao import TargetDAO

logger = logging.getLogger(__name__)

DETECTION_LOG_HEADER: List[str] = [
    "Log ID",
    "Target ID",
    "Target Name",
    "Category",
    "Case Number",
    "Match Confidence",
    "Location",
    "Detection Timestamp",
    "Snapshot Path",
]

TARGET_REGISTRY_HEADER: List[str] = [
    "Target ID",
    "Full Name",
    "Category",
    "Case Number",
    "Status",
    "Description",
    "Profile Image",
    "Created At",
    "Updated At",
]


class ExportService:
    """Service for exporting system data to CSV."""

    @staticmethod
    def export_detection_logs_to_csv(
        output_file_path: str | Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        target_name: Optional[str] = None,
    ) -> int:
        """
        Export detection logs matching filters to a CSV file.

        Args:
            output_file_path: Destination file path.
            start_date: Optional filter start timestamp.
            end_date: Optional filter end timestamp.
            category: Optional filter category.
            target_name: Optional target-name filter. Without this the export
                ignored the name filter shown in the Detection Log view, so the
                CSV silently contained more rows than the table on screen.

        Returns:
            Number of rows exported.
        """
        dest = Path(output_file_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        with get_session() as session:
            logs = DetectionLogDAO.get_recent(
                session,
                limit=10000,
                offset=0,
                category=category,
                start_date=start_date,
                end_date=end_date,
                target_name=target_name,
            )

            with open(dest, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(DETECTION_LOG_HEADER)

                for log in logs:
                    target_full_name = log.target.full_name if log.target else "N/A"
                    category_val = log.target.category if log.target else "N/A"
                    case_no = log.target.case_number if log.target else "N/A"

                    writer.writerow([
                        log.log_id,
                        log.target_id,
                        target_full_name,
                        category_val,
                        case_no,
                        f"{log.match_confidence * 100:.2f}%",
                        log.location_tag or "N/A",
                        log.detection_timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.detection_timestamp else "",
                        log.snapshot_path or "",
                    ])

            logger.info("Exported %d detection logs to %s", len(logs), dest)
            return len(logs)

    @staticmethod
    def export_target_registry_to_csv(
        output_file_path: str | Path,
        category: Optional[str] = None,
        active_only: bool = False,
    ) -> int:
        """
        Export the watchlist registry to a CSV file.

        The module has always advertised registry export; only the detection-log
        half was implemented, which is why TargetDAO was imported but unused.

        Args:
            output_file_path: Destination file path.
            category: Optional category filter (e.g. "CRIMINAL").
            active_only: Export only active targets.

        Returns:
            Number of rows exported.
        """
        dest = Path(output_file_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        with get_session() as session:
            targets = TargetDAO.get_all(session, active_only=active_only)
            if category:
                targets = [t for t in targets if t.category == category]

            with open(dest, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(TARGET_REGISTRY_HEADER)

                for t in targets:
                    writer.writerow([
                        t.target_id,
                        t.full_name,
                        t.category,
                        t.case_number or "N/A",
                        "ACTIVE" if t.is_active else "INACTIVE",
                        (t.description or "").replace("\n", " "),
                        t.profile_image_path or "",
                        t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
                        t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else "",
                    ])

            logger.info("Exported %d registry targets to %s", len(targets), dest)
            return len(targets)
