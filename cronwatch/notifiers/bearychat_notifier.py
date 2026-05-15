"""BearyChat (倍洽) notifier for cronwatch."""
from __future__ import annotations

import urllib.request
import json
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class BearyyChatConfig:
    """Configuration for BearyChat incoming webhook."""

    webhook_url: str
    channel: Optional[str] = None
    # Optional display name override
    bot_name: str = "cronwatch"
    # Timeout in seconds for the HTTP request
    timeout: int = 10


class BearyChatNotifier(BaseNotifier):
    """Send cronwatch alerts to a BearyChat channel via incoming webhook."""

    def __init__(self, config: BearyyChatConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        """POST an alert message to the configured BearyChat webhook."""
        message = self._build_message(payload)
        data = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(
            self._config.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
            if resp.status not in (200, 201, 204):
                raise RuntimeError(
                    f"BearyChat webhook returned HTTP {resp.status}"
                )

    def _build_message(self, payload: AlertPayload) -> dict:
        """Build the BearyChat message payload dict."""
        body: dict = {
            "text": payload.summary(),
            "markdown": True,
        }
        if self._config.channel:
            body["channel"] = self._config.channel
        attachments = [
            {
                "title": f"Job: {payload.job_name}",
                "text": (
                    f"**Reason:** {payload.reason}\n"
                    f"**Failures:** {payload.failure_count}\n"
                    f"**Last seen:** {payload.last_seen or 'never'}"
                ),
                "color": "#FF4444",
            }
        ]
        body["attachments"] = attachments
        return body
