"""
DrishtiX v4.0 — Spatial Face Tracking Manager.

Smooth, drift-free spatial tracker that associates detected faces across frames
using IoU matching and centroid exponential smoothing. Eliminates zombie
trackers and ghost bounding boxes on background textures.
"""

import logging
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


class FaceTrackingManager:
    """
    High-speed spatial face tracker with IoU association and ghost box elimination.
    """

    def __init__(self, max_stale_frames: int = 2) -> None:
        self.max_stale_frames = max_stale_frames  # Prune quickly so no phantom boxes stay
        self._tracks: Dict[int, TrackedFace] = {}
        self._next_track_id: int = 1

    def update_with_detections(self, detections: List[FaceDetection]) -> List[TrackedFace]:
        """
        Update active tracks with fresh detections from the current frame.

        Matches existing tracks using IoU > 0.25 to maintain identity labels
        and smooths bounding box jitter.
        """
        new_tracks: Dict[int, TrackedFace] = {}
        unmatched_dets = list(detections)

        # Match existing tracks with incoming detections
        for track_id, track in self._tracks.items():
            best_iou = 0.0
            best_idx = -1

            for idx, det in enumerate(unmatched_dets):
                iou = calculate_iou(track.bbox, det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = idx

            if best_iou >= 0.25 and best_idx >= 0:
                matched_det = unmatched_dets.pop(best_idx)

                # Smooth bounding box with Exponential Moving Average (EMA) to avoid jitter
                alpha = 0.7  # Weight of new detection
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
        # Return only active (not stale) tracks for rendering
        return [t for t in self._tracks.values() if t.stale_frames == 0]

    def assign_identity(
        self,
        bbox: Tuple[int, int, int, int],
        name: str,
        category: str,
        confidence: float,
    ) -> None:
        """Associate recognition match result with the closest active track."""
        best_track: Optional[TrackedFace] = None
        best_iou = 0.0

        for track in self._tracks.values():
            iou = calculate_iou(track.bbox, bbox)
            if iou > best_iou:
                best_iou = iou
                best_track = track

        if best_track is not None and best_iou >= 0.2:
            best_track.name = name
            best_track.category = category
            best_track.confidence = confidence
            best_track.confirmed = True

    def get_all_active_tracks(self) -> List[TrackedFace]:
        """Return only actively visible tracks from the latest frame."""
        return [t for t in self._tracks.values() if t.stale_frames == 0]

    def clear(self) -> None:
        """Clear all active tracks."""
        self._tracks.clear()
