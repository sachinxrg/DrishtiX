"""
DrishtiX v4.0 — Domain enumerations.

Migrated from the legacy Java TargetCategory enum with additional
status enums for the new Python architecture.
"""

from enum import Enum


class TargetCategory(str, Enum):
    """
    Category classification for watchlist targets.
    Determines bounding box color, alert severity, and sound type.

    Migrated from: com.drishtix.model.TargetCategory (Java)
    """

    CRIMINAL = "CRIMINAL"
    MISSING_PERSON = "MISSING_PERSON"

    @property
    def display_name(self) -> str:
        """Human-readable display label."""
        return self.value.replace("_", " ").title()

    @property
    def box_color_hex(self) -> str:
        """Hex color code for bounding box overlay."""
        return _CATEGORY_COLORS[self]

    @property
    def box_color_bgr(self) -> tuple[int, int, int]:
        """BGR color tuple for OpenCV drawing."""
        return _CATEGORY_COLORS_BGR[self]

    @property
    def sound_file(self) -> str:
        """WAV sound file name for alert playback."""
        return _CATEGORY_SOUNDS[self]


# Private lookup tables — keeps the enum class clean
_CATEGORY_COLORS: dict[TargetCategory, str] = {
    TargetCategory.CRIMINAL: "#FF4D2E",
    TargetCategory.MISSING_PERSON: "#00D4FF",
}

_CATEGORY_COLORS_BGR: dict[TargetCategory, tuple[int, int, int]] = {
    TargetCategory.CRIMINAL: (46, 77, 255),      # #FF4D2E in BGR
    TargetCategory.MISSING_PERSON: (255, 212, 0),  # #00D4FF in BGR
}

_CATEGORY_SOUNDS: dict[TargetCategory, str] = {
    TargetCategory.CRIMINAL: "alarm_criminal.wav",
    TargetCategory.MISSING_PERSON: "chime_missing.wav",
}


class CameraStatus(str, Enum):
    """Camera connection state for status bar display."""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"


class DatabaseStatus(str, Enum):
    """Database connection health state."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class TrackingAlgorithm(str, Enum):
    """Supported object tracking algorithms for inter-frame tracking."""

    KCF = "KCF"
    CSRT = "CSRT"
