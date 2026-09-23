"""
DrishtiX v4.0 — Camera Capture & Detection Worker (QThread).

High-performance video capture and spatial tracking handoff loop.
Aliases VideoThread for backwards compatibility across existing views.
"""

from drishtix.workers.video_thread import VideoThread

class CaptureWorker(VideoThread):
    """
    Video capture and inference worker thread with Facial-to-Spatial Tracking Handoff.
    """
    pass
