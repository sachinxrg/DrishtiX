"""
DrishtiX v4.0 — OSNet Re-ID Model Downloader.

Downloads the OSNet x1.0 ONNX model for whole-body person re-identification.
The model produces 512-dimensional embeddings from body crops.

Source: KaiyangZhou/deep-person-reid (torchreid) — exported to ONNX.
Model: osnet_x1_0 trained on MSMT17 dataset.

Usage:
    python -m drishtix.scripts.download_osnet
    # or from code:
    from drishtix.scripts.download_osnet import ensure_osnet_model
    model_path = ensure_osnet_model()
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Model Configuration ────────────────────────────────────────────────
# OSNet x1.0 trained on MSMT17 — best accuracy/speed trade-off for CPU.
# This is the same architecture referenced in the DnnBodyReIdService.
MODEL_URL = "https://github.com/KaiyangZhou/deep-person-reid/releases/download/v1.1.0/osnet_x1_0_msmt17.onnx"
MODEL_FILENAME = "osnet_x1_0.onnx"
EXPECTED_SHA256 = None  # Set after first successful download for integrity checks

# Where to store the downloaded model
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


def _download_file(url: str, dest: Path, chunk_size: int = 8192) -> None:
    """Download a file with progress reporting."""
    import urllib.request
    import shutil

    logger.info("Downloading OSNet model from: %s", url)
    logger.info("Destination: %s", dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_suffix(".tmp")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DrishtiX/4.0"})
        with urllib.request.urlopen(req, timeout=120) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            with open(tmp_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        if downloaded % (chunk_size * 128) < chunk_size:
                            logger.info("Download progress: %.1f%% (%d / %d bytes)", pct, downloaded, total_size)

        # Rename tmp to final
        tmp_path.rename(dest)
        logger.info("Download complete: %s (%.1f MB)", dest.name, dest.stat().st_size / (1024 * 1024))

    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(f"Failed to download OSNet model: {e}") from e


def _verify_sha256(filepath: Path, expected_hash: str) -> bool:
    """Verify file integrity via SHA-256 hash."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    if actual != expected_hash:
        logger.error("SHA-256 mismatch: expected %s, got %s", expected_hash, actual)
        return False
    return True


def ensure_osnet_model(
    model_dir: Optional[Path] = None,
    force_download: bool = False,
) -> Path:
    """
    Ensure the OSNet ONNX model is available on disk.

    Downloads the model if it doesn't exist. Returns the path to the model file.

    Args:
        model_dir: Directory to store the model. Defaults to drishtix/models/.
        force_download: If True, re-download even if the file exists.

    Returns:
        Path to the OSNet ONNX model file.

    Raises:
        RuntimeError: If download fails.
    """
    target_dir = model_dir or DEFAULT_MODEL_DIR
    model_path = target_dir / MODEL_FILENAME

    if model_path.exists() and not force_download:
        logger.info("OSNet model already exists at: %s", model_path)
        return model_path

    _download_file(MODEL_URL, model_path)

    if EXPECTED_SHA256 is not None:
        if not _verify_sha256(model_path, EXPECTED_SHA256):
            model_path.unlink()
            raise RuntimeError("OSNet model failed SHA-256 integrity check")

    return model_path


def main():
    """CLI entrypoint for downloading the OSNet model."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        path = ensure_osnet_model()
        print(f"\n✅ OSNet Re-ID model ready at: {path}")
        print(f"   Size: {path.stat().st_size / (1024 * 1024):.1f} MB")
    except Exception as e:
        print(f"\n❌ Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
