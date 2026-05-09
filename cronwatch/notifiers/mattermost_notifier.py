"""Mattermost notifier for cronwatch alerts via incoming webhooks."""

from __future__ import annotations

import urllib.request
import urllib.error
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class MattermostConfig:
    """Configuration for the Mattermost notifier."""

    webhook_url: str
    channel: Optional[str] = None  # override default channel, e.g. "#alerts"
    username: str = "cronwatch"
    icon_emoji: str = ":warning:"
    timeout: int = 10
    extra_headers: dict = field(default_factory=dict)


class MattermostNotifier(BaseNotifier):
    """Sends cronwatch alerts to a Mattermost channel via an incoming webhook."""

    def __init__(self, config: MattermostConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self._config
        body = self._build_message(payload)
        data = json.dumps(body).encode()

        req = urllib.request.Request(
            cfg.webhook_url,
            data=data,
            headers={"Content-Type": "application/json", **cfg.extra_headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
                if resp.status not in (200, 201):
                    logger.warning(
                        "Mattermost webhook returned unexpected status %s", resp.status
                    )
        except urllib.error.URLError as exc:
            logger.error("Failed to send Mattermost alert: %s", exc)

    def _build_message(self, payload: AlertPayload) -> dict:
        cfg = self._config
        text = (
            f"**cronwatch alert** — {payload.summary()}\n"
            f"Job: `{payload.job_name}` | Reason: {payload.reason}"
        )
        if payload.last_seen:
            text += f" | Last seen: {payload.last_seen.isoformat()}"

        message: dict = {
            "text": text,
            "username": cfg.username,
            "icon_emoji": cfg.icon_emoji,
        }
        if cfg.channel:
            message["channel"] = cfg.channel
        return message
