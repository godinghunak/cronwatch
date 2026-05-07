"""VictorOps (Splunk On-Call) notifier for cronwatch alerts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10
_MESSAGE_TYPE_CRITICAL = "CRITICAL"
_MESSAGE_TYPE_INFO = "INFO"


@dataclass
class VictorOpsConfig:
    """Configuration for the VictorOps notifier."""

    routing_key: str
    rest_endpoint: str  # e.g. https://alert.victorops.com/integrations/generic/…/alert
    timeout: int = _DEFAULT_TIMEOUT
    extra_fields: Dict[str, Any] = field(default_factory=dict)


class VictorOpsNotifier(BaseNotifier):
    """Send alerts to VictorOps via the REST endpoint API."""

    def __init__(self, config: VictorOpsConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        url = f"{self._config.rest_endpoint.rstrip('/')}/{self._config.routing_key}"
        body = self._build_event(payload)
        try:
            response = requests.post(
                url,
                json=body,
                timeout=self._config.timeout,
            )
            response.raise_for_status()
            logger.info(
                "VictorOps alert sent for job '%s' (status %s)",
                payload.job_name,
                response.status_code,
            )
        except requests.RequestException as exc:
            logger.error("VictorOps notification failed: %s", exc)

    def _build_event(self, payload: AlertPayload) -> Dict[str, Any]:
        event: Dict[str, Any] = {
            "message_type": _MESSAGE_TYPE_CRITICAL,
            "entity_id": f"cronwatch/{payload.job_name}",
            "entity_display_name": f"cronwatch: {payload.job_name}",
            "state_message": payload.summary(),
            "monitoring_tool": "cronwatch",
            "job_name": payload.job_name,
            "reason": payload.reason,
        }
        if payload.last_seen is not None:
            event["last_seen"] = payload.last_seen.isoformat()
        event.update(self._config.extra_fields)
        return event
