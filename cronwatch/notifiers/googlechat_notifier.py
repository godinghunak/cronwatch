"""Google Chat notifier for cronwatch alerts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import urllib.request
import urllib.error
import json
import logging

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class GoogleChatConfig:
    """Configuration for Google Chat webhook notifier."""

    webhook_url: str
    timeout: int = 10
    extra_headers: dict[str, str] = field(default_factory=dict)


class GoogleChatNotifier(BaseNotifier):
    """Sends cronwatch alerts to a Google Chat space via an incoming webhook."""

    def __init__(self, config: GoogleChatConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        message = self._build_message(payload)
        body = json.dumps(message).encode()
        headers = {"Content-Type": "application/json", **self._config.extra_headers}

        req = urllib.request.Request(
            self._config.webhook_url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                status = resp.status
                if status != 200:
                    logger.warning(
                        "GoogleChatNotifier: unexpected status %s for job '%s'",
                        status,
                        payload.job_name,
                    )
                else:
                    logger.debug(
                        "GoogleChatNotifier: alert sent for job '%s'", payload.job_name
                    )
        except urllib.error.URLError as exc:
            logger.error(
                "GoogleChatNotifier: failed to send alert for job '%s': %s",
                payload.job_name,
                exc,
            )

    def _build_message(self, payload: AlertPayload) -> dict[str, Any]:
        """Build a Google Chat card message from an AlertPayload."""
        return {
            "cards": [
                {
                    "header": {
                        "title": f"cronwatch alert: {payload.job_name}",
                        "subtitle": payload.reason,
                    },
                    "sections": [
                        {
                            "widgets": [
                                {"textParagraph": {"text": payload.summary()}},
                            ]
                        }
                    ],
                }
            ]
        }
