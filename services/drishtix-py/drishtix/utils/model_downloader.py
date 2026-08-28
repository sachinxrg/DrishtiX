"""
DrishtiX v4.0 — ONNX Model Downloader.

Utility to verify and automatically download official OpenCV Zoo YuNet & SFace ONNX models.
"""

import logging
from pathlib import Path
from typing import Optional

import httpx

from drishtix.core.constants import (
    MODELS_DIR,
    SFACE_MODEL_FILE,
    YUNET_MODEL_FILE,
)

logger = logging.getLogger(__name__)

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"


def ensure_models(dest_dir: Optional[Path] = None) -> bool:
    """
    Ensure YuNet and SFace ONNX models are present in the models directory.
    Downloads them if missing.

    Args:
        dest_dir: Target directory (defaults to MODELS_DIR).

    Returns:
        True if all models are present or downloaded successfully.
    """
    target_dir = dest_dir or MODELS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    yunet_path = target_dir / YUNET_MODEL_FILE
    sface_path = target_dir / SFACE_MODEL_FILE

    success = True

    if not yunet_path.exists():
        logger.info("Downloading YuNet model to %s...", yunet_path)
        if not _download_file(YUNET_URL, yunet_path):
            success = False

    if not sface_path.exists():
        logger.info("Downloading SFace model to %s...", sface_path)
        if not _download_file(SFACE_URL, sface_path):
            success = False

    return success


def _download_file(url: str, dest: Path) -> bool:
    """Download file with follow_redirects."""
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                logger.info("Downloaded %s (%d bytes)", dest.name, len(resp.content))
                return True
            else:
                logger.warning("Failed to download from %s: HTTP %d", url, resp.status_code)
                return False
    except Exception as e:
        logger.warning("Download error for %s: %s", url, e)
        return False
