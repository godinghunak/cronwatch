"""Telegram notifier — sends alerts via the Telegram Bot API."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


@dataclass
class TelegramConfig:
    """Configuration for the Telegram notifier."""

    bot_token: str
    chat_ids: List[str] = field(default_factory=list)
    parse_mode: str = "Markdown"  # "Markdown" or "HTML"
    timeout: int = 10


class TelegramNotifier(BaseNotifier):
    """Send alert messages to one or more Telegram chats."""

    def __init__(self, config: TelegramConfig) -> None:
        self._config = config
        self._url = TELEGRAM_API_BASE.format(token=config.bot_token)

    def send(self, payload: AlertPayload) -> None:
        if not self._config.chat_ids:
            logger.warning("TelegramNotifier: no chat_ids configured, skipping.")
            return

        text = self._build_message(payload)
        for chat_id in self._config.chat_ids:
            self._post(chat_id, text)

    def _build_message(self, payload: AlertPayload) -> str:
        lines = [
            f"*[cronwatch] {payload.job_name}*",
            f"Reason: {payload.reason}",
            f"Triggered at: {payload.triggered_at.isoformat()}",
        ]
        if payload.last_seen:
            lines.append(f"Last seen: {payload.last_seen.isoformat()}")
        if payload.details:
            lines.append(f"Details: {payload.details}")
        return "\n".join(lines)

    def _post(self, chat_id: str, text: str) -> None:
        body = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": self._config.parse_mode,
        }
        try:
            resp = requests.post(self._url, json=body, timeout=self._config.timeout)
            resp.raise_for_status()
            logger.debug("TelegramNotifier: message sent to chat %s", chat_id)
        except requests.RequestException as exc:
            logger.error("TelegramNotifier: failed to send to chat %s: %s", chat_id, exc)
