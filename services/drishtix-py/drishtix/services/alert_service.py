"""
DrishtiX v4.0 — Tactical Alert Service.

Coordinates alert generation, audio playback, database persistence,
per-target cooldown suppression, and snapshot saving.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import asyncio

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
from drishtix.services.telegram_service import TelegramService
from drishtix.utils.image_utils import mat_to_qpixmap, safe_crop
from drishtix.utils.sound_player import SoundPlayer

logger = logging.getLogger(__name__)


class AlertService:
    """
    Coordinates alert generation, cooldowns, and multi-frame confirmation.

    Multi-Frame Confirmation (§5.4):
        To prevent single-frame false positives from triggering tactical alerts,
        a target must be matched in N consecutive frames within a time window
        before an alert is actually fired. This trades ~100-200ms latency for
        dramatically reduced false alert rate.
    """

    _instance: Optional["AlertService"] = None

    # Confirmation thresholds
    CONFIRMATION_THRESHOLD = 2        # Number of consecutive frames required
    CONFIRMATION_WINDOW_SECONDS = 5.0  # Max time window for confirmations

    def __init__(self, cooldown_seconds: int = DEFAULT_ALERT_COOLDOWN_SECONDS) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time: Dict[int, float] = {}  # target_id -> timestamp
        self._sound_player = SoundPlayer.get_instance()
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        # Shared executor for Telegram dispatch — bounds thread creation to 1
        # background thread instead of spawning a new thread per alert (B8 fix).
        self._telegram_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="telegram")

        # Multi-frame confirmation state (§5.4)
        # Maps target_id -> (hit_count, first_hit_timestamp)
        self._confirmation_state: Dict[int, Tuple[int, float]] = {}

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

    def _check_confirmation(self, target_id: int) -> bool:
        """
        Multi-frame confirmation gate (§5.4).

        Tracks consecutive match hits per target within a sliding window.
        Returns True only when the target has been matched in at least
        CONFIRMATION_THRESHOLD frames within CONFIRMATION_WINDOW_SECONDS.

        Args:
            target_id: The matched target's ID.

        Returns:
            True if the target is confirmed (alert should fire), False to wait.
        """
        now = time.time()
        state = self._confirmation_state.get(target_id)

        if state is None:
            # First hit for this target
            self._confirmation_state[target_id] = (1, now)
            return self.CONFIRMATION_THRESHOLD <= 1

        hit_count, first_hit_time = state

        if (now - first_hit_time) > self.CONFIRMATION_WINDOW_SECONDS:
            # Window expired — reset counter
            self._confirmation_state[target_id] = (1, now)
            return self.CONFIRMATION_THRESHOLD <= 1

        # Within window — increment
        new_count = hit_count + 1
        self._confirmation_state[target_id] = (new_count, first_hit_time)

        if new_count >= self.CONFIRMATION_THRESHOLD:
            # Confirmed — reset for next cycle
            del self._confirmation_state[target_id]
            return True

        return False

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
            Alert payload dictionary if alert was triggered, None if suppressed.
        """
        target = match.target
        target_id = target.target_id

        # Cooldown check
        if self.is_in_cooldown(target_id):
            logger.debug("Alert suppressed by cooldown for target: %s (id=%d)", target.full_name, target_id)
            return None

        # Multi-frame confirmation gate (§5.4): require N consecutive frames
        if not self._check_confirmation(target_id):
            logger.debug(
                "Alert pending confirmation for target: %s (id=%d)",
                target.full_name, target_id,
            )
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

        # Dispatch Telegram notification via shared executor (avoids B8: thread-per-alert)
        tele_svc = TelegramService.get_instance()
        if tele_svc.enabled:
            # Capture values for the closure
            _name = target.full_name
            _cat = target.category
            _case = target.case_number or "N/A"
            _conf = match.confidence
            _loc = location_tag or "Unknown"
            _snap = snapshot_path

            def _send_telegram():
                try:
                    asyncio.run(tele_svc.send_alert_async(
                        full_name=_name,
                        category=_cat,
                        case_number=_case,
                        confidence=_conf,
                        location=_loc,
                        snapshot_path=_snap,
                    ))
                except Exception as e:
                    logger.error("Telegram dispatch failed: %s", e)

            self._telegram_executor.submit(_send_telegram)

        return alert_payload
