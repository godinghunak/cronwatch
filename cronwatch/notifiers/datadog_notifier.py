from __future__ import annotations

import urllib.request
import urllib.error
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

DATADOG_EVENTS_URL = "https://api.datadoghq.com/api/v1/events"


@dataclass
class DatadogConfig:
    api_key: str
    app_key: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    host: Optional[str] = None
    # Allow EU or custom Datadog site endpoints
    base_url: str = DATADOG_EVENTS_URL


class DatadogNotifier(BaseNotifier):
    """Send cron job alerts to Datadog as events."""

    def __init__(self, config: DatadogConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        event = self._build_event(payload)
        body = json.dumps(event).encode()

        headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self._config.api_key,
        }
        if self._config.app_key:
            headers["DD-APPLICATION-KEY"] = self._config.app_key

        req = urllib.request.Request(
            self._config.base_url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
            logger.info("Datadog event posted for job '%s' (HTTP %s)", payload.job_name, status)
        except urllib.error.HTTPError as exc:
            logger.error(
                "Datadog HTTP error for job '%s': %s %s",
                payload.job_name,
                exc.code,
                exc.reason,
            )
        except urllib.error.URLError as exc:
            logger.error("Datadog URL error for job '%s': %s", payload.job_name, exc.reason)

    def _build_event(self, payload: AlertPayload) -> dict:
        tags = list(self._config.tags) + [f"job:{payload.job_name}"]
        event: dict = {
            "title": f"cronwatch: {payload.job_name} – {payload.reason}",
            "text": payload.summary(),
            "alert_type": "error",
            "source_type_name": "cronwatch",
            "tags": tags,
        }
        if self._config.host:
            event["host"] = self._config.host
        return event
