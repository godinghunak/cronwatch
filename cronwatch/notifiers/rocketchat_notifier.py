from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class RocketChatConfig:
    """Configuration for Rocket.Chat incoming webhook notifier."""

    webhook_url: str
    channel: str = ""
    username: str = "cronwatch"
    icon_emoji: str = ":alarm_clock:"
    timeout: int = 10
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.webhook_url:
            raise ValueError("webhook_url must not be empty")


class RocketChatNotifier(BaseNotifier):
    """Send cronwatch alerts to a Rocket.Chat channel via an incoming webhook."""

    def __init__(self, config: RocketChatConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        message = self._build_message(payload)
        response = requests.post(
            self.config.webhook_url,
            json=message,
            timeout=self.config.timeout,
        )
        response.raise_for_status()

    def _build_message(self, payload: AlertPayload) -> dict[str, Any]:
        body: dict[str, Any] = {
            "text": payload.summary(),
            "username": self.config.username,
            "emoji": self.config.icon_emoji,
        }
        if self.config.channel:
            body["channel"] = self.config.channel
        body.update(self.config.extra_fields)
        return body
