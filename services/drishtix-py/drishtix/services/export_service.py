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


class ExportService:
    """Service for exporting system data to CSV."""

    @staticmethod
    def export_detection_logs_to_csv(
        output_file_path: str | Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Export detection logs matching filters to a CSV file.

        Args:
            output_file_path: Destination file path.
            start_date: Optional filter start timestamp.
            end_date: Optional filter end timestamp.
            category: Optional filter category.

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
            )

            with open(dest, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow([
                    "Log ID",
                    "Target ID",
                    "Target Name",
                    "Category",
                    "Case Number",
                    "Match Confidence",
                    "Location",
                    "Detection Timestamp",
                    "Snapshot Path",
                ])

                for log in logs:
                    target_name = log.target.full_name if log.target else "N/A"
                    category_val = log.target.category if log.target else "N/A"
                    case_no = log.target.case_number if log.target else "N/A"

                    writer.writerow([
                        log.log_id,
                        log.target_id,
                        target_name,
                        category_val,
                        case_no,
                        f"{log.match_confidence * 100:.2f}%",
                        log.location_tag or "N/A",
                        log.detection_timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.detection_timestamp else "",
                        log.snapshot_path or "",
                    ])

            logger.info("Exported %d detection logs to %s", len(logs), dest)
            return len(logs)
