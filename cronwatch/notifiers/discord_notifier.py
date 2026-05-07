from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class DiscordConfig:
    """Configuration for Discord webhook notifications."""

    webhook_url: str
    username: str = "CronWatch"
    avatar_url: Optional[str] = None
    timeout: int = 10
    # Optional role/user IDs to mention, e.g. ["<@&123456>", "<@789012>"]
    mentions: list[str] = field(default_factory=list)


class DiscordNotifier(BaseNotifier):
    """Send cron-job alerts to a Discord channel via an incoming webhook."""

    def __init__(self, config: DiscordConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        """POST an alert message to the configured Discord webhook URL."""
        message = self._build_message(payload)
        body: dict = {
            "username": self.config.username,
            "content": message,
        }
        if self.config.avatar_url:
            body["avatar_url"] = self.config.avatar_url

        try:
            response = requests.post(
                self.config.webhook_url,
                json=body,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            logger.debug("Discord notification sent for job '%s'", payload.job_name)
        except requests.RequestException as exc:
            logger.error(
                "Failed to send Discord notification for job '%s': %s",
                payload.job_name,
                exc,
            )

    def _build_message(self, payload: AlertPayload) -> str:
        """Compose the text content sent to Discord."""
        mention_str = " ".join(self.config.mentions)
        prefix = f"{mention_str}\n" if mention_str else ""
        return (
            f"{prefix}"
            f":warning: **CronWatch Alert**\n"
            f"{payload.summary()}"
        )
