"""
DrishtiX v4.0 — RTSP Camera Source with Automatic Reconnection.

Wraps cv2.VideoCapture for RTSP/RTMP network camera streams with:
1. Exponential backoff reconnection (1s → 2s → 4s → ... → 30s max)
2. Connection health monitoring via frame timeout detection
3. Stream metadata extraction (resolution, FPS, codec)
4. Thread-safe status queries

Usage:
    source = RtspSource("rtsp://admin:pass@192.168.1.100:554/stream1")
    source.connect()

    while source.is_connected:
        frame = source.read()
        if frame is not None:
            process(frame)

    source.release()
"""

import logging
import time
import threading
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────
INITIAL_RECONNECT_DELAY_S = 1.0
MAX_RECONNECT_DELAY_S = 30.0
BACKOFF_MULTIPLIER = 2.0
FRAME_TIMEOUT_S = 10.0          # Consider stream dead after this many seconds without frames
MAX_CONSECUTIVE_FAILURES = 100  # Max read() failures before triggering reconnect


@dataclass
class StreamInfo:
    """Metadata about the connected stream."""

    url: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    codec: str = ""
    is_connected: bool = False
    reconnect_count: int = 0
    last_frame_time: float = 0.0


class RtspSource:
    """
    Network camera source with automatic reconnection.

    Designed for RTSP/RTMP/HTTP streams that may drop intermittently
    due to network issues, camera reboots, or bandwidth constraints.
    """

    def __init__(
        self,
        url: str,
        buffer_size: int = 1,
        connection_timeout_ms: int = 10000,
    ) -> None:
        self._url = url
        self._buffer_size = buffer_size
        self._connection_timeout_ms = connection_timeout_ms
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._connected = False
        self._reconnect_count = 0
        self._last_frame_time = 0.0
        self._consecutive_failures = 0
        self._current_delay = INITIAL_RECONNECT_DELAY_S

    @property
    def is_connected(self) -> bool:
        """Thread-safe connection status query."""
        with self._lock:
            return self._connected

    @property
    def stream_info(self) -> StreamInfo:
        """Return current stream metadata."""
        with self._lock:
            info = StreamInfo(
                url=self._url,
                is_connected=self._connected,
                reconnect_count=self._reconnect_count,
                last_frame_time=self._last_frame_time,
            )
            if self._cap is not None and self._cap.isOpened():
                info.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info.fps = self._cap.get(cv2.CAP_PROP_FPS)
                fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
                info.codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return info

    def connect(self) -> bool:
        """
        Establish connection to the RTSP stream.

        Returns:
            True if connection was successful.
        """
        with self._lock:
            return self._connect_internal()

    def _connect_internal(self) -> bool:
        """Internal connection logic (must hold self._lock)."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass

        logger.info("Connecting to RTSP stream: %s", self._url)

        # Set environment for RTSP over TCP (more reliable than UDP)
        cap = cv2.VideoCapture(self._url, cv2.CAP_FFMPEG)

        if not cap or not cap.isOpened():
            logger.error("Failed to connect to RTSP stream: %s", self._url)
            self._connected = False
            return False

        # Configure for low-latency streaming
        cap.set(cv2.CAP_PROP_BUFFERSIZE, self._buffer_size)

        self._cap = cap
        self._connected = True
        self._consecutive_failures = 0
        self._last_frame_time = time.monotonic()

        info = StreamInfo(
            url=self._url,
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=cap.get(cv2.CAP_PROP_FPS),
            is_connected=True,
        )
        logger.info(
            "RTSP connected: %dx%d @ %.1f FPS (reconnects: %d)",
            info.width, info.height, info.fps, self._reconnect_count,
        )
        return True

    def read(self) -> Optional[np.ndarray]:
        """
        Read a frame from the stream.

        Returns None and triggers reconnection logic on failure.
        """
        with self._lock:
            if self._cap is None or not self._connected:
                return None

            # Check for frame timeout (stream may be hung)
            if (time.monotonic() - self._last_frame_time) > FRAME_TIMEOUT_S:
                logger.warning("Frame timeout (%.0fs). Triggering reconnect.", FRAME_TIMEOUT_S)
                self._trigger_reconnect()
                return None

            ret, frame = self._cap.read()

            if not ret or frame is None or frame.size == 0:
                self._consecutive_failures += 1
                if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        "Stream failure: %d consecutive read failures. Reconnecting.",
                        self._consecutive_failures,
                    )
                    self._trigger_reconnect()
                return None

            self._consecutive_failures = 0
            self._last_frame_time = time.monotonic()
            self._current_delay = INITIAL_RECONNECT_DELAY_S  # Reset backoff on success
            return frame

    def _trigger_reconnect(self) -> None:
        """Attempt reconnection with exponential backoff (must hold self._lock)."""
        self._connected = False
        self._reconnect_count += 1

        logger.info(
            "Reconnect attempt #%d (delay: %.1fs)...",
            self._reconnect_count, self._current_delay,
        )

        # Release current connection
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        # Sleep with backoff (release lock during sleep)
        delay = self._current_delay
        self._current_delay = min(
            self._current_delay * BACKOFF_MULTIPLIER,
            MAX_RECONNECT_DELAY_S,
        )

        # Note: we hold the lock here, which blocks reads during reconnect.
        # This is acceptable because reads would fail anyway.
        time.sleep(delay)
        self._connect_internal()

    def release(self) -> None:
        """Release the stream and clean up resources."""
        with self._lock:
            self._connected = False
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            logger.info(
                "RTSP source released: %s (total reconnects: %d)",
                self._url, self._reconnect_count,
            )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.release()
