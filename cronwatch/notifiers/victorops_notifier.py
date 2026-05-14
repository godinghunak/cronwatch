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
class VictorOpsConfig:
    routing_key: str
    rest_endpoint_url: str  # e.g. https://alert.victorops.com/integrations/generic/…/alert/<api_key>
    message_type: str = "CRITICAL"
    timeout: int = 10


class VictorOpsNotifier(BaseNotifier):
    def __init__(self, config: VictorOpsConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        event = self._build_event(payload)
        url = f"{self.config.rest_endpoint_url.rstrip('/')}/{self.config.routing_key}"
        data = json.dumps(event).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                status = resp.status
                logger.info("VictorOps alert sent for job '%s', status=%s", payload.job_name, status)
        except urllib.error.HTTPError as exc:
            logger.error("VictorOps HTTP error for job '%s': %s", payload.job_name, exc)
        except urllib.error.URLError as exc:
            logger.error("VictorOps URL error for job '%s': %s", payload.job_name, exc)

    def _build_event(self, payload: AlertPayload) -> dict:
        return {
            "message_type": self.config.message_type,
            "entity_id": f"cronwatch/{payload.job_name}",
            "entity_display_name": f"cronwatch: {payload.job_name}",
            "state_message": payload.summary(),
            "monitoring_tool": "cronwatch",
            "timestamp": int(payload.triggered_at.timestamp()),
            "details": {
                "reason": payload.reason,
                "last_seen": payload.last_seen.isoformat() if payload.last_seen else None,
                "consecutive_failures": payload.consecutive_failures,
            },
        }
