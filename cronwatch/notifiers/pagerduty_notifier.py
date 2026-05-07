"""PagerDuty notifier — sends alerts via the PagerDuty Events API v2."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

PAGERDUTY_EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"


@dataclass
class PagerDutyConfig:
    """Configuration for the PagerDuty notifier."""

    integration_key: str  # Routing key for the Events API v2 integration
    severity: str = "error"  # critical | error | warning | info
    source: str = "cronwatch"
    timeout: int = 10
    extra_details: dict = field(default_factory=dict)


class PagerDutyNotifier(BaseNotifier):
    """Send alerts to PagerDuty using the Events API v2."""

    def __init__(self, config: PagerDutyConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        body = self._build_event(payload)
        try:
            response = requests.post(
                PAGERDUTY_EVENTS_URL,
                json=body,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            logger.info(
                "PagerDuty alert sent for job '%s' (dedup_key=%s)",
                payload.job_name,
                body["dedup_key"],
            )
        except requests.RequestException as exc:
            logger.error("Failed to send PagerDuty alert for '%s': %s", payload.job_name, exc)

    def _build_event(self, payload: AlertPayload) -> dict:
        details: dict = {
            "reason": payload.reason,
            "last_seen": payload.last_seen.isoformat() if payload.last_seen else None,
            "consecutive_failures": payload.consecutive_failures,
        }
        details.update(self.config.extra_details)

        return {
            "routing_key": self.config.integration_key,
            "event_action": "trigger",
            "dedup_key": f"cronwatch-{payload.job_name}",
            "payload": {
                "summary": payload.summary(),
                "source": self.config.source,
                "severity": self.config.severity,
                "custom_details": details,
            },
        }
