"""
DrishtiX v4.0 — Telegram Notification Service.

Asynchronously pushes tactical alert notifications and snapshots
to a Telegram channel / chat via Telegram Bot API.
Migrated from: com.drishtix.service.TelegramAlertService (Java)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import threading
import httpx

logger = logging.getLogger(__name__)


class TelegramService:
    """Dispatches tactical alert notifications to Telegram."""

    _instance: Optional["TelegramService"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        bot_token: str = "",
        chat_id: str = "",
        enabled: bool = False,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled

    @classmethod
    def get_instance(cls) -> "TelegramService":
        """Thread-safe singleton accessor."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def update_config(self, bot_token: str, chat_id: str, enabled: bool) -> None:
        """Update Telegram credentials."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled

    async def send_alert_async(
        self,
        full_name: str,
        category: str,
        case_number: str,
        confidence: float,
        location: str,
        snapshot_path: Optional[str | Path] = None,
    ) -> bool:
        """
        Send formatted alert message and optional photo to Telegram asynchronously.
        """
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False

        caption = (
            f"🚨 <b>DRISHTIX TACTICAL ALERT</b>\n\n"
            f"<b>Target:</b> {full_name}\n"
            f"<b>Category:</b> {category}\n"
            f"<b>Case/FIR:</b> {case_number}\n"
            f"<b>Confidence:</b> {confidence * 100:.1f}%\n"
            f"<b>Location:</b> {location}\n"
            f"<b>Timestamp:</b> <code>{Path(__file__).name}</code>"
        )

        base_url = f"https://api.telegram.org/bot{self.bot_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if snapshot_path and Path(snapshot_path).exists():
                    url = f"{base_url}/sendPhoto"
                    with open(snapshot_path, "rb") as photo_file:
                        files = {"photo": photo_file}
                        data = {
                            "chat_id": self.chat_id,
                            "caption": caption,
                            "parse_mode": "HTML",
                        }
                        resp = await client.post(url, data=data, files=files)
                else:
                    url = f"{base_url}/sendMessage"
                    payload = {
                        "chat_id": self.chat_id,
                        "text": caption,
                        "parse_mode": "HTML",
                    }
                    resp = await client.post(url, json=payload)

                if resp.status_code == 200:
                    logger.info("Telegram alert dispatched successfully for target: %s", full_name)
                    return True
                else:
                    logger.warning("Telegram API error (%d): %s", resp.status_code, resp.text)
                    return False
        except Exception as e:
            logger.error("Failed to send Telegram notification: %s", e)
            return False
