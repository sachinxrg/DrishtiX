"""
DrishtiX v4.0 — Sound player utility.

Non-blocking audio alert playback using PySide6.QtMultimedia.QSoundEffect
with fallback to winsound (Windows) for zero-dependency operation.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from drishtix.core.constants import ASSETS_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)


class SoundPlayer:
    """Non-blocking sound player for tactical alerts."""

    _instance: Optional["SoundPlayer"] = None

    def __init__(self) -> None:
        self._effects: dict[str, QSoundEffect] = {}
        self._enabled: bool = True

    @classmethod
    def get_instance(cls) -> "SoundPlayer":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = SoundPlayer()
        return cls._instance

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable audio alerts."""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self._enabled

    def play(self, sound_filename: str) -> None:
        """
        Play a WAV sound file asynchronously.

        Args:
            sound_filename: Name of the wav file (e.g. 'alarm_criminal.wav').
        """
        if not self._enabled:
            return

        sound_path = self._resolve_sound_path(sound_filename)
        if not sound_path or not sound_path.exists():
            logger.warning("Sound file not found: %s", sound_filename)
            return

        try:
            # Try QSoundEffect
            if sound_filename not in self._effects:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(sound_path.resolve())))
                effect.setVolume(1.0)
                self._effects[sound_filename] = effect

            effect = self._effects[sound_filename]
            effect.play()
            logger.debug("Playing sound: %s", sound_filename)
        except Exception as e:
            logger.debug("QSoundEffect play failed, trying native fallback: %s", e)
            self._play_fallback(sound_path)

    def _play_fallback(self, sound_path: Path) -> None:
        """Fallback to winsound on Windows if QtMultimedia encounters issues."""
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as ex:
                logger.error("Failed to play sound via winsound: %s", ex)

    def _resolve_sound_path(self, sound_filename: str) -> Optional[Path]:
        """Search for sound file in standard asset locations."""
        candidates = [
            ASSETS_DIR / "sounds" / sound_filename,
            PROJECT_ROOT / "services" / "drishtix-app" / "src" / "main" / "resources" / "sounds" / sound_filename,
            PROJECT_ROOT / "resources" / "sounds" / sound_filename,
            Path("assets/sounds") / sound_filename,
        ]
        for c in candidates:
            if c.exists():
                return c
        return None
