"""
DrishtiX v4.0 — Pydantic Settings configuration model.

Loads and validates configuration from config.yaml with environment variable
overrides (prefixed with DRISHTIX_). Replaces the legacy Java config.properties
with typed, validated settings.
"""

from pathlib import Path
from typing import Union

import yaml
from pydantic import BaseModel, Field, field_validator


class AppSettings(BaseModel):
    """Application identity and logging configuration."""

    name: str = "DrishtiX v4.0"
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels}")
        return upper


class CameraSettings(BaseModel):
    """Camera source and capture configuration."""

    source: Union[int, str] = 0
    resolution: tuple[int, int] = (1280, 720)
    target_fps: int = Field(default=30, ge=1, le=120)


class DetectionSettings(BaseModel):
    """YuNet face detection model configuration."""

    model_path: str = "models/face_detection_yunet_2023mar.onnx"
    score_threshold: float = Field(default=0.6, ge=0.1, le=1.0)
    nms_threshold: float = Field(default=0.3, ge=0.1, le=1.0)
    inference_interval: int = Field(default=3, ge=1, le=10)


class RecognitionSettings(BaseModel):
    """SFace face recognition model configuration."""

    model_path: str = "models/face_recognition_sface_2021dec.onnx"
    match_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    pool_size: int = Field(default=4, ge=1, le=16)


class AlertSettings(BaseModel):
    """Alert system configuration."""

    cooldown_seconds: int = Field(default=30, ge=0, le=3600)
    max_queue_size: int = Field(default=50, ge=10, le=200)
    sound_enabled: bool = True
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


class DatabaseSettings(BaseModel):
    """SQLite database configuration."""

    path: str = "data/drishtix.db"


class TrackingSettings(BaseModel):
    """Inter-frame face tracking configuration."""

    algorithm: str = "KCF"
    max_stale_frames: int = Field(default=10, ge=1, le=60)

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        valid = {"KCF", "CSRT"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"Invalid tracking algorithm '{v}'. Must be one of: {valid}")
        return upper


class DrishtiXSettings(BaseModel):
    """
    Root configuration model aggregating all subsections.

    Loaded from config.yaml at startup with environment variable overrides.
    """

    app: AppSettings = AppSettings()
    camera: CameraSettings = CameraSettings()
    detection: DetectionSettings = DetectionSettings()
    recognition: RecognitionSettings = RecognitionSettings()
    alerts: AlertSettings = AlertSettings()
    database: DatabaseSettings = DatabaseSettings()
    tracking: TrackingSettings = TrackingSettings()


def load_settings(config_path: Union[str, Path] = "config.yaml") -> DrishtiXSettings:
    """
    Load settings from a YAML configuration file.

    Falls back to default values if the file is not found.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated DrishtiXSettings instance.
    """
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return DrishtiXSettings(**raw)

    # No config file found — use all defaults
    return DrishtiXSettings()


# Module-level singleton — lazily initialized
_settings: DrishtiXSettings | None = None


def get_settings() -> DrishtiXSettings:
    """Return the global settings singleton, loading from config.yaml on first call."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings(config_path: Union[str, Path] = "config.yaml") -> DrishtiXSettings:
    """Force-reload settings from disk. Used when config.yaml is modified at runtime."""
    global _settings
    _settings = load_settings(config_path)
    return _settings
