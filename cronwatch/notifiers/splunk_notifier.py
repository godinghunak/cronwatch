"""Splunk HTTP Event Collector (HEC) notifier for cronwatch."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class SplunkConfig:
    """Configuration for Splunk HEC notifier."""

    hec_url: str  # e.g. "https://splunk.example.com:8088/services/collector/event"
    token: str
    index: Optional[str] = None
    source: str = "cronwatch"
    sourcetype: str = "cronwatch:alert"
    timeout: int = 10
    verify_ssl: bool = True
    extra_fields: dict = field(default_factory=dict)


class SplunkNotifier(BaseNotifier):
    """Sends cronwatch alerts to a Splunk HEC endpoint."""

    def __init__(self, config: SplunkConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self._config
        event = self._build_event(payload)
        headers = {
            "Authorization": f"Splunk {cfg.token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            cfg.hec_url,
            json=event,
            headers=headers,
            timeout=cfg.timeout,
            verify=cfg.verify_ssl,
        )
        response.raise_for_status()

    def _build_event(self, payload: AlertPayload) -> dict:
        cfg = self._config
        event_body = {
            "job": payload.job_name,
            "reason": payload.reason,
            "summary": payload.summary(),
            "last_seen": payload.last_seen.isoformat() if payload.last_seen else None,
            "consecutive_failures": payload.consecutive_failures,
            **cfg.extra_fields,
        }
        hec_event: dict = {
            "time": time.time(),
            "source": cfg.source,
            "sourcetype": cfg.sourcetype,
            "event": event_body,
        }
        if cfg.index:
            hec_event["index"] = cfg.index
        return hec_event
