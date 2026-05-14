"""Zulip notifier for cronwatch alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class ZulipConfig:
    """Configuration for the Zulip notifier."""

    site_url: str  # e.g. "https://yourorg.zulipchat.com"
    bot_email: str
    bot_api_key: str
    stream: str
    topic: str = "cronwatch alerts"
    timeout: int = 10

    def __post_init__(self) -> None:
        self.site_url = self.site_url.rstrip("/")


class ZulipNotifier(BaseNotifier):
    """Send cronwatch alerts to a Zulip stream via the Zulip REST API."""

    def __init__(self, config: ZulipConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self._config
        url = f"{cfg.site_url}/api/v1/messages"
        data = self._build_message(payload)
        try:
            resp = requests.post(
                url,
                auth=(cfg.bot_email, cfg.bot_api_key),
                data=data,
                timeout=cfg.timeout,
            )
            resp.raise_for_status()
            logger.debug("Zulip notification sent for job %s", payload.job_name)
        except requests.RequestException as exc:
            logger.error("Zulip notification failed for job %s: %s", payload.job_name, exc)

    def _build_message(self, payload: AlertPayload) -> dict:
        return {
            "type": "stream",
            "to": self._config.stream,
            "topic": self._config.topic,
            "content": payload.summary(),
        }
