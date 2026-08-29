"""
DrishtiX v4.0 — Sound Player Utility.

High-performance, non-blocking audio alert playback using native Windows Multimedia (winsound)
with cross-platform fallback to PySide6.QtMultimedia.QSoundEffect.
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from drishtix.core.constants import ASSETS_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)


class SoundPlayer:
    """Non-blocking tactical siren and audio alert player."""

    _instance: Optional["SoundPlayer"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._effects: dict[str, QSoundEffect] = {}
        self._enabled: bool = True

    @classmethod
    def get_instance(cls) -> "SoundPlayer":
        """Thread-safe singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = SoundPlayer()
            return cls._instance

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable audio alerts."""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self._enabled

    def play_siren(self) -> None:
        """Convenience method to trigger the emergency tactical siren."""
        self.play("alarm_criminal.wav")

    def play(self, sound_filename: str) -> None:
        """
        Play a WAV audio alert file asynchronously.

        Args:
            sound_filename: Name of the wav file (e.g. 'alarm_criminal.wav' or 'siren.wav').
        """
        if not self._enabled:
            return

        sound_path = self._resolve_sound_path(sound_filename)
        if not sound_path or not sound_path.exists():
            logger.warning("Sound file not found: %s", sound_filename)
            return

        # 1. Native Windows Sound Engine (Zero latency, direct thread-safe playback)
        if sys.platform == "win32":
            try:
                import winsound
                resolved_str = str(sound_path.resolve())
                # Play asynchronously without blocking the calling thread
                winsound.PlaySound(resolved_str, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                logger.info("Played tactical sound via winsound: %s", sound_filename)
                return
            except Exception as e:
                logger.debug("winsound playback failed: %s, falling back to QtMultimedia", e)

        # 2. PySide6 QSoundEffect fallback
        try:
            if sound_filename not in self._effects:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(sound_path.resolve())))
                effect.setVolume(1.0)
                self._effects[sound_filename] = effect

            effect = self._effects[sound_filename]
            effect.play()
            logger.info("Played tactical sound via QSoundEffect: %s", sound_filename)
        except Exception as ex:
            logger.error("All audio backends failed for %s: %s", sound_filename, ex)

    def _resolve_sound_path(self, sound_filename: str) -> Optional[Path]:
        """Search for sound file in standard asset locations."""
        candidates = [
            ASSETS_DIR / "sounds" / sound_filename,
            Path("assets/sounds") / sound_filename,
            PROJECT_ROOT / "assets" / "sounds" / sound_filename,
            Path(__file__).resolve().parent.parent.parent / "assets" / "sounds" / sound_filename,
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()
        return None
