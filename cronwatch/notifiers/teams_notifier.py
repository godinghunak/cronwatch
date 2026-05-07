"""Microsoft Teams notifier via Incoming Webhook."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class TeamsConfig:
    webhook_url: str
    timeout: int = 10
    mention_emails: List[str] = field(default_factory=list)


class TeamsNotifier(BaseNotifier):
    """Send alerts to a Microsoft Teams channel via an Incoming Webhook."""

    def __init__(self, config: TeamsConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        if not self.config.webhook_url:
            logger.warning("TeamsNotifier: webhook_url is not configured; skipping.")
            return

        body = self._build_message(payload)
        try:
            response = requests.post(
                self.config.webhook_url,
                json=body,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            logger.info("TeamsNotifier: alert sent for job '%s'.", payload.job_name)
        except requests.RequestException as exc:
            logger.error("TeamsNotifier: failed to send alert: %s", exc)

    def _build_message(self, payload: AlertPayload) -> dict:
        mentions = ""
        if self.config.mention_emails:
            mentions = " ".join(
                f"<at>{email}</at>" for email in self.config.mention_emails
            )

        text = payload.summary()
        if mentions:
            text = f"{mentions} {text}"

        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"cronwatch alert: {payload.job_name}",
            "themeColor": "FF0000",
            "title": f"\u26a0\ufe0f cronwatch alert: {payload.job_name}",
            "text": text,
            "sections": [
                {
                    "facts": [
                        {"name": "Job", "value": payload.job_name},
                        {"name": "Reason", "value": payload.reason},
                        {
                            "name": "Last seen",
                            "value": payload.last_seen.isoformat()
                            if payload.last_seen
                            else "never",
                        },
                        {"name": "Consecutive failures", "value": str(payload.consecutive_failures)},
                    ]
                }
            ],
        }
