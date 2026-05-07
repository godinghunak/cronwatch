"""Slack notifier that sends alert payloads to a Slack webhook URL."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class SlackConfig:
    webhook_url: str
    channel: Optional[str] = None  # overrides the webhook default channel
    username: str = "CronWatch"
    icon_emoji: str = ":warning:"
    timeout_seconds: float = 10.0


class SlackNotifier(BaseNotifier):
    """Sends alerts to a Slack incoming webhook."""

    def __init__(self, config: SlackConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        if not self.config.webhook_url:
            logger.warning("SlackNotifier: webhook_url is not configured; skipping.")
            return

        message = self._build_message(payload)
        body = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(
            self.config.webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                status = resp.status
            logger.info("SlackNotifier: alert sent for job %r (HTTP %s).", payload.job_name, status)
        except urllib.error.URLError as exc:
            logger.error("SlackNotifier: failed to send alert for job %r: %s", payload.job_name, exc)

    def _build_message(self, payload: AlertPayload) -> dict:
        message: dict = {
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "text": payload.summary(),
        }
        if self.config.channel:
            message["channel"] = self.config.channel
        return message
