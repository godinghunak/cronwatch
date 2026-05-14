"""ntfy.sh notifier for cronwatch alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class NtfyConfig:
    """Configuration for the ntfy notifier."""

    topic: str
    server: str = "https://ntfy.sh"
    token: Optional[str] = None
    priority: str = "high"  # min, low, default, high, urgent
    tags: list[str] = field(default_factory=lambda: ["rotating_light"])
    timeout: int = 10

    def __post_init__(self) -> None:
        if not self.topic:
            raise ValueError("ntfy topic must not be empty")
        valid_priorities = {"min", "low", "default", "high", "urgent"}
        if self.priority not in valid_priorities:
            raise ValueError(
                f"priority must be one of {valid_priorities}, got {self.priority!r}"
            )


class NtfyNotifier(BaseNotifier):
    """Send cronwatch alerts to a ntfy.sh topic."""

    def __init__(self, config: NtfyConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        url = f"{self.config.server.rstrip('/')}/{self.config.topic}"

        headers: dict[str, str] = {
            "Title": f"[cronwatch] {payload.job_name} — {payload.reason}",
            "Priority": self.config.priority,
            "Tags": ",".join(self.config.tags),
        }
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        body = payload.summary()

        response = requests.post(
            url,
            data=body.encode("utf-8"),
            headers=headers,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
