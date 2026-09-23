"""
DrishtiX v4.0 — Spatial Face Tracking Manager.

Smooth, drift-free spatial tracker that associates detected faces across frames
using IoU matching, centroid proximity, and exponential smoothing.
Maintains thread-safe identity persistence across frames without flickering.
"""

import logging
import math
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from drishtix.services.face_detection import FaceDetection

logger = logging.getLogger(__name__)


@dataclass
class TrackedFace:
    """State for a tracked face across frames."""

    track_id: int
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    name: str = "Unknown"
    category: Optional[str] = None
    confidence: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    stale_frames: int = 0
    confirmed: bool = False


def calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Calculate Intersection-over-Union (IoU) between two bounding boxes (x, y, w, h)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter_area = inter_w * inter_h

    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    union_area = boxAArea + boxBArea - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / float(union_area)


def calculate_center_distance(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Calculate Euclidean distance between box centroids."""
    cA_x = boxA[0] + (boxA[2] / 2.0)
    cA_y = boxA[1] + (boxA[3] / 2.0)
    cB_x = boxB[0] + (boxB[2] / 2.0)
    cB_y = boxB[1] + (boxB[3] / 2.0)
    return math.hypot(cA_x - cB_x, cA_y - cB_y)


class FaceTrackingManager:
    """
    High-speed spatial face tracker with IoU and centroid association.
    Thread-safe and preserves confirmed identity states across frames.
    """

    def __init__(self, max_stale_frames: int = 6) -> None:
        self.max_stale_frames = max_stale_frames
        self._tracks: Dict[int, TrackedFace] = {}
        self._next_track_id: int = 1
        self._lock = threading.Lock()

    def update_with_detections(self, detections: List[FaceDetection]) -> List[TrackedFace]:
        """
        Update active tracks with fresh detections from the current frame.
        """
        with self._lock:
            new_tracks: Dict[int, TrackedFace] = {}
            unmatched_dets = list(detections)

            # Match existing tracks with incoming detections
            for track_id, track in self._tracks.items():
                best_iou = 0.0
                best_dist = float("inf")
                best_idx = -1

                track_max_dim = max(track.bbox[2], track.bbox[3], 1)

                for idx, det in enumerate(unmatched_dets):
                    iou = calculate_iou(track.bbox, det.bbox)
                    dist = calculate_center_distance(track.bbox, det.bbox)

                    if iou > best_iou:
                        best_iou = iou
                        best_idx = idx
                    elif best_iou < 0.15 and dist < best_dist and dist < (track_max_dim * 0.85):
                        best_dist = dist
                        best_idx = idx

                # If matched by IoU or Proximity
                if (best_iou >= 0.15 or best_dist < (track_max_dim * 0.85)) and best_idx >= 0:
                    matched_det = unmatched_dets.pop(best_idx)

                    # Smooth bounding box with Exponential Moving Average (EMA)
                    alpha = 0.75
                    old_x, old_y, old_w, old_h = track.bbox
                    new_x, new_y, new_w, new_h = matched_det.bbox

                    smooth_bbox = (
                        int(round(alpha * new_x + (1 - alpha) * old_x)),
                        int(round(alpha * new_y + (1 - alpha) * old_y)),
                        int(round(alpha * new_w + (1 - alpha) * old_w)),
                        int(round(alpha * new_h + (1 - alpha) * old_h)),
                    )

                    track.bbox = smooth_bbox
                    track.stale_frames = 0
                    new_tracks[track_id] = track
                else:
                    # Face was not detected in this frame
                    track.stale_frames += 1
                    if track.stale_frames <= self.max_stale_frames:
                        new_tracks[track_id] = track

            # Create new tracks for newly appeared faces
            for det in unmatched_dets:
                track_id = self._next_track_id
                self._next_track_id += 1

                new_tracks[track_id] = TrackedFace(
                    track_id=track_id,
                    bbox=det.bbox,
                    name="Unknown",
                    category=None,
                    confidence=None,
                    stale_frames=0,
                    confirmed=False,
                )

            self._tracks = new_tracks
            return [t for t in self._tracks.values() if t.stale_frames <= 2]

    def assign_identity(
        self,
        bbox: Tuple[int, int, int, int],
        name: str,
        category: str,
        confidence: float,
        age: Optional[int] = None,
        gender: Optional[str] = None,
    ) -> None:
        """
        Associate recognition match result with the closest active track (thread-safe).
        """
        with self._lock:
            if not self._tracks:
                return

            best_track: Optional[TrackedFace] = None
            best_iou = 0.0
            best_dist = float("inf")

            box_max_dim = max(bbox[2], bbox[3], 1)

            for track in self._tracks.values():
                iou = calculate_iou(track.bbox, bbox)
                dist = calculate_center_distance(track.bbox, bbox)

                if iou > best_iou:
                    best_iou = iou
                    best_track = track
                elif best_iou < 0.15 and dist < best_dist and dist < (box_max_dim * 1.5):
                    best_dist = dist
                    best_track = track

            # If only 1 track exists in the entire frame, associate directly
            if best_track is None and len(self._tracks) == 1:
                best_track = next(iter(self._tracks.values()))

            if best_track is not None:
                best_track.name = name
                best_track.category = category
                best_track.confidence = confidence
                if age is not None:
                    best_track.age = age
                if gender is not None:
                    best_track.gender = gender
                best_track.confirmed = True
                logger.debug("Assigned identity %s (%s) to track %d", name, category, best_track.track_id)

    def get_all_active_tracks(self) -> List[TrackedFace]:
        """Return only actively visible tracks from recent frames (thread-safe)."""
        with self._lock:
            return [
                TrackedFace(
                    track_id=t.track_id,
                    bbox=t.bbox,
                    name=t.name,
                    category=t.category,
                    confidence=t.confidence,
                    age=t.age,
                    gender=t.gender,
                    stale_frames=t.stale_frames,
                    confirmed=t.confirmed,
                )
                for t in self._tracks.values()
                if t.stale_frames <= 2
            ]

    def clear(self) -> None:
        """Clear all active tracks."""
        with self._lock:
            self._tracks.clear()
