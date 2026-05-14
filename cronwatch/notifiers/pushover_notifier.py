"""Pushover notifier for cronwatch alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


@dataclass
class PushoverConfig:
    """Configuration for the Pushover notifier."""

    api_token: str
    user_keys: List[str] = field(default_factory=list)
    priority: int = 0  # -2 (lowest) to 2 (emergency)
    sound: str = "falling"
    timeout: int = 10

    def __post_init__(self) -> None:
        if self.priority < -2 or self.priority > 2:
            raise ValueError("priority must be between -2 and 2")


class PushoverNotifier(BaseNotifier):
    """Send cronwatch alerts via Pushover push notifications."""

    def __init__(self, config: PushoverConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        if not self._config.user_keys:
            return

        title = f"cronwatch: {payload.job_name}"
        message = payload.summary()

        for user_key in self._config.user_keys:
            body = self._build_body(user_key, title, message)
            resp = requests.post(
                PUSHOVER_API_URL,
                data=body,
                timeout=self._config.timeout,
            )
            resp.raise_for_status()

    def _build_body(self, user_key: str, title: str, message: str) -> dict:
        return {
            "token": self._config.api_token,
            "user": user_key,
            "title": title,
            "message": message,
            "priority": self._config.priority,
            "sound": self._config.sound,
        }
