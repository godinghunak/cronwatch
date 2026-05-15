"""Gotify notifier — sends alerts to a self-hosted Gotify server."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class GotifyConfig:
    """Configuration for the Gotify notifier."""

    server_url: str  # e.g. "https://gotify.example.com"
    app_token: str
    priority: int = 5
    timeout: int = 10
    extra_headers: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.server_url = self.server_url.rstrip("/")
        if not self.server_url:
            raise ValueError("GotifyConfig.server_url must not be empty")
        if not self.app_token:
            raise ValueError("GotifyConfig.app_token must not be empty")


class GotifyNotifier(BaseNotifier):
    """Send cronwatch alerts to a Gotify push notification server."""

    def __init__(self, config: GotifyConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self._config
        url = f"{cfg.server_url}/message"

        headers = {
            "X-Gotify-Key": cfg.app_token,
            "Content-Type": "application/json",
            **cfg.extra_headers,
        }

        body = self._build_message(payload)

        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=cfg.timeout,
        )
        response.raise_for_status()

    def _build_message(self, payload: AlertPayload) -> dict:
        return {
            "title": f"[cronwatch] {payload.job_name} — {payload.reason}",
            "message": payload.summary(),
            "priority": self._config.priority,
            "extras": {
                "client::display": {"contentType": "text/plain"},
            },
        }
