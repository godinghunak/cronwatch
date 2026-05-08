from __future__ import annotations

import urllib.request
import urllib.error
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class GrafanaConfig:
    """Configuration for Grafana Alerting webhook (Grafana 8+ unified alerting)."""

    url: str  # Grafana webhook URL, e.g. https://grafana.example.com/api/alerts
    api_key: Optional[str] = None  # Bearer token for authenticated instances
    tags: List[str] = field(default_factory=list)  # Extra labels attached to every alert
    timeout: int = 10


class GrafanaNotifier(BaseNotifier):
    """Send alerts to a Grafana webhook endpoint."""

    def __init__(self, config: GrafanaConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        body = self._build_event(payload)
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            self.config.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.config.api_key:
            req.add_header("Authorization", f"Bearer {self.config.api_key}")

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                status = resp.status
                logger.info("GrafanaNotifier: alert sent, HTTP %s", status)
        except urllib.error.HTTPError as exc:
            logger.error("GrafanaNotifier: HTTP error %s — %s", exc.code, exc.reason)
        except urllib.error.URLError as exc:
            logger.error("GrafanaNotifier: URL error — %s", exc.reason)

    def _build_event(self, payload: AlertPayload) -> dict:
        labels = {"job": payload.job_name, "reason": payload.reason}
        for tag in self.config.tags:
            if ":" in tag:
                k, v = tag.split(":", 1)
                labels[k.strip()] = v.strip()

        annotations = {"summary": payload.summary()}
        if payload.last_seen:
            annotations["last_seen"] = payload.last_seen.isoformat()
        if payload.schedule:
            annotations["schedule"] = payload.schedule

        return {
            "title": f"[cronwatch] {payload.job_name} — {payload.reason}",
            "state": "alerting",
            "labels": labels,
            "annotations": annotations,
        }
