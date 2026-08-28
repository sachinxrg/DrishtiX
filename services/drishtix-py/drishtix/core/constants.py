"""
DrishtiX v4.0 — Application-wide constants.

All magic numbers and default values are centralized here to avoid
scattering configuration across the codebase. Runtime-configurable values
are loaded from config.yaml via the Settings model; these constants serve
as compile-time defaults and structural limits.
"""

from pathlib import Path

# ─── Application Identity ──────────────────────────────────────────
APP_NAME = "DrishtiX v4.0"
APP_VERSION = "4.0.0"

# ─── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
GALLERY_DIR = DATA_DIR / "gallery"

# ─── ONNX Model Files ──────────────────────────────────────────────
YUNET_MODEL_FILE = "face_detection_yunet_2023mar.onnx"
SFACE_MODEL_FILE = "face_recognition_sface_2021dec.onnx"

# ─── Detection Defaults ────────────────────────────────────────────
DEFAULT_SCORE_THRESHOLD = 0.65       # YuNet confidence threshold
DEFAULT_NMS_THRESHOLD = 0.3          # Non-max suppression threshold
DEFAULT_INFERENCE_INTERVAL = 1       # Run YuNet every frame (sub-3ms inference)
DEFAULT_MATCH_THRESHOLD = 0.58       # SFace cosine similarity threshold (prevents false matches)

# ─── Face Recognition ──────────────────────────────────────────────
SFACE_EMBEDDING_DIM = 128             # SFace output vector dimensionality
SFACE_INPUT_SIZE = (112, 112)         # Aligned face crop input resolution
EMBEDDING_BYTE_SIZE = SFACE_EMBEDDING_DIM * 4  # 128 float32s → 512 bytes

# ─── Alert System ──────────────────────────────────────────────────
DEFAULT_ALERT_COOLDOWN_SECONDS = 30
MAX_ALERT_QUEUE_SIZE = 50

# ─── Threading ──────────────────────────────────────────────────────
RECOGNITION_POOL_SIZE = 4
CAPTURE_TARGET_FPS = 30

# ─── Tracking ──────────────────────────────────────────────────────
MAX_STALE_TRACKER_FRAMES = 10

# ─── UI Layout ──────────────────────────────────────────────────────
NAV_SIDEBAR_WIDTH = 220
ALERT_SIDEBAR_WIDTH = 380
STATUS_BAR_HEIGHT = 32
ALERT_CARD_THUMBNAIL_SIZE = 64
STATUS_UPDATE_INTERVAL_MS = 500

# ─── Camera ─────────────────────────────────────────────────────────
DEFAULT_CAMERA_SOURCE = 0
DEFAULT_RESOLUTION = (1280, 720)
CAMERA_RECONNECT_INTERVAL_MS = 3000

# ─── Database ──────────────────────────────────────────────────────
DEFAULT_DB_PATH = "data/drishtix.db"

# ─── Bounding Box Colors (BGR for OpenCV, Hex for UI) ──────────────
CRIMINAL_COLOR_BGR = (46, 77, 255)     # #FF4D2E in BGR
CRIMINAL_COLOR_HEX = "#FF4D2E"
MISSING_COLOR_BGR = (255, 212, 0)      # #00D4FF in BGR
MISSING_COLOR_HEX = "#00D4FF"
UNKNOWN_COLOR_BGR = (128, 128, 128)
UNKNOWN_COLOR_HEX = "#808080"

# ─── Sound Files ────────────────────────────────────────────────────
CRIMINAL_ALARM_FILE = "alarm_criminal.wav"
MISSING_CHIME_FILE = "chime_missing.wav"
