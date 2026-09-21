"""
DrishtiX v4.0 — Pydantic Settings configuration model.

Loads and validates configuration from config.yaml. Replaces the legacy Java
config.properties with typed, validated settings.

Assignment is validated (`validate_assignment=True`) so runtime edits made from
the Settings view are still checked against each field's constraints, and
`save_settings()` writes the active configuration back to config.yaml.
"""

from pathlib import Path
from typing import Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from drishtix.core.constants import PROJECT_ROOT


class _StrictModel(BaseModel):
    """
    Shared base for every settings section.

    - `validate_assignment` makes Field(ge=..., le=...) constraints apply to
      runtime mutation, not just construction.
    - `protected_namespaces=()` allows the `model_path` / `model_pack` fields;
      Pydantic v2 otherwise emits a UserWarning for any `model_*` attribute.
    """

    model_config = ConfigDict(validate_assignment=True, protected_namespaces=())


class AppSettings(_StrictModel):
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


class CameraSettings(_StrictModel):
    """Camera source and capture configuration."""

    source: Union[int, str] = 0
    resolution: tuple[int, int] = (1280, 720)
    target_fps: int = Field(default=30, ge=1, le=120)


class DetectionSettings(_StrictModel):
    """YuNet face detection model configuration."""

    model_path: str = "models/face_detection_yunet_2023mar.onnx"
    score_threshold: float = Field(default=0.6, ge=0.1, le=1.0)
    nms_threshold: float = Field(default=0.3, ge=0.1, le=1.0)
    inference_interval: int = Field(default=3, ge=1, le=10)


class RecognitionSettings(_StrictModel):
    """Face recognition model configuration (SFace or InsightFace)."""

    engine: str = "sface"                 # "sface" (128-D) or "insightface" (512-D)
    model_pack: str = "buffalo_s"         # "buffalo_s" or "buffalo_l"
    model_path: str = "models/face_recognition_sface_2021dec.onnx"
    match_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    pool_size: int = Field(default=4, ge=1, le=16)

    @field_validator("engine")
    @classmethod
    def validate_engine(cls, v: str) -> str:
        valid = {"sface", "insightface"}
        lower = v.lower()
        if lower not in valid:
            raise ValueError(f"Invalid recognition engine '{v}'. Must be one of: {valid}")
        return lower


class AlertSettings(_StrictModel):
    """Alert system configuration."""

    cooldown_seconds: int = Field(default=30, ge=0, le=3600)
    max_queue_size: int = Field(default=50, ge=10, le=200)
    sound_enabled: bool = True
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    snapshot_retention_days: int = Field(default=30, ge=1, le=365, description="Auto-delete snapshots older than this")


class DatabaseSettings(_StrictModel):
    """SQLite database configuration."""

    path: str = "data/drishtix.db"
    log_retention_days: int = Field(default=30, ge=1, le=365, description="Auto-delete detection logs older than this")
    encryption_key: str = Field(default="", description="SQLCipher encryption key. Empty = no encryption.")


class TrackingSettings(_StrictModel):
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


class DrishtiXSettings(_StrictModel):
    """
    Root configuration model aggregating all subsections.

    Loaded from config.yaml at startup.
    """

    app: AppSettings = AppSettings()
    camera: CameraSettings = CameraSettings()
    detection: DetectionSettings = DetectionSettings()
    recognition: RecognitionSettings = RecognitionSettings()
    alerts: AlertSettings = AlertSettings()
    database: DatabaseSettings = DatabaseSettings()
    tracking: TrackingSettings = TrackingSettings()


# Anchored to the project root rather than the current working directory.
# As a bare relative name this resolved against wherever the process happened
# to be launched from, so starting the app from any other directory silently
# loaded stock defaults instead of the operator's config (camera source, match
# thresholds, Telegram credentials, database path) — and save_settings() then
# wrote a stray config.yaml into that directory rather than updating the real
# one.
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_settings(config_path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> DrishtiXSettings:
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


def save_settings(
    settings: "DrishtiXSettings | None" = None,
    config_path: Union[str, Path] = DEFAULT_CONFIG_PATH,
) -> Path:
    """
    Write the active settings back to a YAML configuration file.

    Without this, edits made in the Settings view live only in memory and are
    silently lost on restart.

    Args:
        settings: Settings to persist. Defaults to the active singleton.
        config_path: Destination YAML file.

    Returns:
        The path written to.
    """
    target = settings if settings is not None else get_settings()
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    payload = target.model_dump(mode="json")
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
    return config_file


# Module-level singleton — lazily initialized
_settings: DrishtiXSettings | None = None


def get_settings() -> DrishtiXSettings:
    """Return the global settings singleton, loading from config.yaml on first call."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings(config_path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> DrishtiXSettings:
    """Force-reload settings from disk. Used when config.yaml is modified at runtime."""
    global _settings
    _settings = load_settings(config_path)
    return _settings
