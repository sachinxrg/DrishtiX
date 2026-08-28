"""
DrishtiX v4.0 — Tactical Alert Service.

Coordinates alert generation, audio playback, database persistence,
per-target cooldown suppression, and snapshot saving.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from drishtix.core.constants import (
    DEFAULT_ALERT_COOLDOWN_SECONDS,
    SNAPSHOTS_DIR,
)
from drishtix.core.enums import TargetCategory
from drishtix.core.signals import signal_bus
from drishtix.dao.detection_log_dao import DetectionLogDAO
from drishtix.dao.session import get_session
from drishtix.models.detection_log import DetectionLog
from drishtix.services.gallery_manager import MatchResult
from drishtix.utils.image_utils import mat_to_qpixmap, safe_crop
from drishtix.utils.sound_player import SoundPlayer

logger = logging.getLogger(__name__)


class AlertService:
    """
    Coordinates alert generation and cooldowns.
    """

    _instance: Optional["AlertService"] = None

    def __init__(self, cooldown_seconds: int = DEFAULT_ALERT_COOLDOWN_SECONDS) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time: Dict[int, float] = {}  # target_id -> timestamp
        self._sound_player = SoundPlayer.get_instance()
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "AlertService":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = AlertService()
        return cls._instance

    def set_cooldown_seconds(self, seconds: int) -> None:
        """Update cooldown period in seconds."""
        self.cooldown_seconds = max(0, seconds)

    def is_in_cooldown(self, target_id: int) -> bool:
        """Check if target alert is currently suppressed by cooldown."""
        now = time.time()
        last = self._last_alert_time.get(target_id, 0.0)
        return (now - last) < self.cooldown_seconds

    def process_match(
        self,
        match: MatchResult,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        camera_id: Optional[int] = None,
        location_tag: Optional[str] = "Main Entrance",
    ) -> Optional[dict]:
        """
        Process a positive face recognition match.

        1. Checks per-target cooldown.
        2. Saves cropped face snapshot to data/snapshots/.
        3. Persists DetectionLog to SQLite database.
        4. Triggers category-specific WAV sound alert.
        5. Emits signal_bus.alert_created for UI sidebar card rendering.

        Args:
            match: The MatchResult object.
            frame: Full BGR video frame.
            bbox: (x, y, w, h) bounding box.
            camera_id: Optional source camera id.
            location_tag: String location identifier.

        Returns:
            Alert payload dictionary if alert was triggered, None if cooldown suppressed.
        """
        target = match.target
        target_id = target.target_id

        # Cooldown check
        if self.is_in_cooldown(target_id):
            logger.debug("Alert suppressed by cooldown for target: %s (id=%d)", target.full_name, target_id)
            return None

        self._last_alert_time[target_id] = time.time()
        now_dt = datetime.now()

        # Save snapshot
        snapshot_filename = f"det_{target_id}_{int(time.time())}.jpg"
        snapshot_path = SNAPSHOTS_DIR / snapshot_filename
        crop = safe_crop(frame, bbox, padding_ratio=0.15)

        if crop is not None and crop.size > 0:
            try:
                cv2.imwrite(str(snapshot_path), crop)
            except Exception as e:
                logger.error("Failed to save snapshot: %s", e)
                snapshot_path = None
        else:
            snapshot_path = None

        rel_snapshot_str = str(snapshot_path.relative_to(Path.cwd())) if snapshot_path and snapshot_path.exists() else None

        # Persist to database
        log_entry_id = None
        try:
            with get_session() as session:
                log_entry = DetectionLog(
                    target_id=target_id,
                    camera_id=camera_id,
                    match_confidence=match.confidence,
                    snapshot_path=rel_snapshot_str,
                    location_tag=location_tag,
                    detection_timestamp=now_dt,
                )
                DetectionLogDAO.create(session, log_entry)
                log_entry_id = log_entry.log_id
        except Exception as e:
            logger.error("Failed to log detection to database: %s", e)

        # Audio playback
        category_enum = None
        try:
            category_enum = TargetCategory(target.category.upper())
            sound_file = category_enum.sound_file
            self._sound_player.play(sound_file)
        except Exception as e:
            logger.debug("Sound playback error: %s", e)

        # Build UI payload
        crop_pixmap = mat_to_qpixmap(crop) if crop is not None else None

        alert_payload = {
            "log_id": log_entry_id,
            "target_id": target_id,
            "full_name": target.full_name,
            "category": target.category,
            "case_number": target.case_number or "N/A",
            "confidence": match.confidence,
            "snapshot": crop_pixmap,
            "snapshot_path": rel_snapshot_str,
            "timestamp": now_dt,
            "bbox": bbox,
            "location_tag": location_tag,
        }

        # Emit signal to UI
        signal_bus.alert_created.emit(alert_payload)
        logger.info(
            "TACTICAL ALERT TRIGGERED: Target '%s' [%s] Confidence: %.1f%% (Log #%s)",
            target.full_name,
            target.category,
            match.confidence * 100,
            log_entry_id,
        )

        return alert_payload
