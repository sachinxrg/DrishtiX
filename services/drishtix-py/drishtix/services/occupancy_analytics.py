"""
DrishtiX v4.0 — Occupancy Analytics Service.

Tracks real-time zone occupancy by counting unique face detections within
configurable time windows. Provides:
1. Current occupancy count (unique faces in the last N seconds)
2. Peak occupancy with timestamp
3. Hourly occupancy histogram for trend analysis
4. Occupancy alerts when thresholds are exceeded

Uses tracked face IDs from FaceTrackingManager to avoid double-counting
the same person across consecutive frames.
"""

import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from drishtix.core.signals import signal_bus

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────
DEFAULT_WINDOW_SECONDS = 60      # Count unique faces within this window
DEFAULT_MAX_OCCUPANCY = 50       # Alert threshold


@dataclass
class OccupancySnapshot:
    """Point-in-time occupancy measurement."""

    timestamp: float
    current_count: int
    peak_count: int
    peak_timestamp: float
    window_seconds: int


@dataclass
class HourlyBucket:
    """Aggregated occupancy metrics for one hour."""

    hour: int                     # 0-23
    date: str                     # YYYY-MM-DD
    total_detections: int = 0
    unique_faces: int = 0
    peak_occupancy: int = 0


class OccupancyAnalytics:
    """
    Real-time occupancy tracking and analytics.

    Maintains a sliding window of tracked face observations to compute
    current occupancy. Uses track IDs to deduplicate the same person
    appearing in consecutive frames.
    """

    _instance: Optional["OccupancyAnalytics"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        max_occupancy: int = DEFAULT_MAX_OCCUPANCY,
    ) -> None:
        self._window_seconds = window_seconds
        self._max_occupancy = max_occupancy
        self._lock = threading.Lock()

        # Sliding window: track_id -> last_seen_timestamp
        self._active_tracks: Dict[int, float] = {}

        # Peak tracking
        self._peak_count: int = 0
        self._peak_timestamp: float = 0.0

        # Hourly histogram: "YYYY-MM-DD-HH" -> HourlyBucket
        self._hourly_buckets: Dict[str, HourlyBucket] = {}

        # Total detection counter
        self._total_detections: int = 0

    @classmethod
    def get_instance(cls) -> "OccupancyAnalytics":
        """Thread-safe singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def record_detections(self, track_ids: List[int]) -> OccupancySnapshot:
        """
        Record face track observations for occupancy counting.

        Args:
            track_ids: List of active track IDs from FaceTrackingManager.

        Returns:
            Current occupancy snapshot.
        """
        now = time.time()

        with self._lock:
            # Update active tracks with current observations
            for tid in track_ids:
                self._active_tracks[tid] = now

            # Expire stale tracks outside the window
            cutoff = now - self._window_seconds
            self._active_tracks = {
                tid: ts for tid, ts in self._active_tracks.items()
                if ts >= cutoff
            }

            current_count = len(self._active_tracks)

            # Update peak
            if current_count > self._peak_count:
                self._peak_count = current_count
                self._peak_timestamp = now

            # Update hourly bucket
            self._total_detections += len(track_ids)
            dt = datetime.fromtimestamp(now)
            bucket_key = dt.strftime("%Y-%m-%d-%H")
            if bucket_key not in self._hourly_buckets:
                self._hourly_buckets[bucket_key] = HourlyBucket(
                    hour=dt.hour,
                    date=dt.strftime("%Y-%m-%d"),
                )
            bucket = self._hourly_buckets[bucket_key]
            bucket.total_detections += len(track_ids)
            bucket.unique_faces = max(bucket.unique_faces, current_count)
            bucket.peak_occupancy = max(bucket.peak_occupancy, current_count)

            # Occupancy threshold alert
            if current_count >= self._max_occupancy:
                logger.warning(
                    "Occupancy threshold exceeded: %d / %d",
                    current_count, self._max_occupancy,
                )

            return OccupancySnapshot(
                timestamp=now,
                current_count=current_count,
                peak_count=self._peak_count,
                peak_timestamp=self._peak_timestamp,
                window_seconds=self._window_seconds,
            )

    def get_current_occupancy(self) -> int:
        """Return current unique face count within the window."""
        now = time.time()
        cutoff = now - self._window_seconds
        with self._lock:
            return sum(1 for ts in self._active_tracks.values() if ts >= cutoff)

    def get_peak(self) -> Tuple[int, float]:
        """Return (peak_count, peak_timestamp)."""
        with self._lock:
            return self._peak_count, self._peak_timestamp

    def get_hourly_histogram(self, date: Optional[str] = None) -> List[HourlyBucket]:
        """
        Get hourly occupancy buckets for a specific date.

        Args:
            date: Date string "YYYY-MM-DD". Defaults to today.

        Returns:
            List of HourlyBucket objects for the requested date.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            return [
                b for b in self._hourly_buckets.values()
                if b.date == date
            ]

    def reset(self) -> None:
        """Reset all counters and history."""
        with self._lock:
            self._active_tracks.clear()
            self._peak_count = 0
            self._peak_timestamp = 0.0
            self._hourly_buckets.clear()
            self._total_detections = 0
            logger.info("Occupancy analytics reset.")
