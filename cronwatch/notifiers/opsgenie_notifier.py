"""OpsGenie notifier for cronwatch alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

OPSGENIE_ALERT_URL = "https://api.opsgenie.com/v2/alerts"


@dataclass
class OpsGenieConfig:
    api_key: str
    responders: list[dict] = field(default_factory=list)  # e.g. [{"type": "team", "name": "ops"}]
    tags: list[str] = field(default_factory=list)
    priority: str = "P3"  # P1–P5
    timeout: int = 10


class OpsGenieNotifier(BaseNotifier):
    """Send alerts to OpsGenie via the REST API."""

    def __init__(self, config: OpsGenieConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        headers = {
            "Authorization": f"GenieKey {self.config.api_key}",
            "Content-Type": "application/json",
        }
        body = self._build_alert(payload)
        try:
            resp = requests.post(
                OPSGENIE_ALERT_URL,
                json=body,
                headers=headers,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            logger.info("OpsGenie alert sent for job '%s'", payload.job_name)
        except requests.HTTPError as exc:
            logger.error(
                "OpsGenie notification failed for job '%s': HTTP %s - %s",
                payload.job_name,
                exc.response.status_code if exc.response is not None else "unknown",
                exc.response.text if exc.response is not None else exc,
            )
        except requests.RequestException as exc:
            logger.error("OpsGenie notification failed for job '%s': %s", payload.job_name, exc)

    def _build_alert(self, payload: AlertPayload) -> dict:
        return {
            "message": f"[cronwatch] {payload.job_name}: {payload.reason}",
            "alias": f"cronwatch-{payload.job_name}",
            "description": payload.summary(),
            "responders": self.config.responders,
            "tags": self.config.tags,
            "priority": self.config.priority,
            "details": {
                "job_name": payload.job_name,
                "reason": payload.reason,
                "last_seen": payload.last_seen.isoformat() if payload.last_seen else "never",
                "exit_code": str(payload.exit_code) if payload.exit_code is not None else "n/a",
            },
        }

    def close_alert(self, job_name: str) -> None:
        """Close (resolve) an existing OpsGenie alert by its alias.

        This is useful after a previously failing job recovers successfully,
        allowing cronwatch to auto-resolve the open incident.
        """
        alias = f"cronwatch-{job_name}"
        url = f"{OPSGENIE_ALERT_URL}/{alias}/close"
        headers = {
            "Authorization": f"GenieKey {self.config.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                url,
                json={"note": "Resolved automatically by cronwatch."},
                headers=headers,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            logger.info("OpsGenie alert closed for job '%s'", job_name)
        except requests.HTTPError as exc:
            logger.error(
                "OpsGenie close alert failed for job '%s': HTTP %s - %s",
                job_name,
                exc.response.status_code if exc.response is not None else "unknown",
                exc.response.text if exc.response is not None else exc,
            )
        except requests.RequestException as exc:
            logger.error("OpsGenie close alert failed for job '%s': %s", job_name, exc)
