"""SignalWire SMS notifier for cronwatch alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class SignalWireConfig:
    """Configuration for the SignalWire notifier."""

    space_url: str  # e.g. "example.signalwire.com"
    project_id: str
    api_token: str
    from_number: str
    to_numbers: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.space_url:
            raise ValueError("space_url must not be empty")
        if not self.project_id:
            raise ValueError("project_id must not be empty")
        if not self.api_token:
            raise ValueError("api_token must not be empty")
        if not self.from_number:
            raise ValueError("from_number must not be empty")


class SignalWireNotifier(BaseNotifier):
    """Send SMS alerts via the SignalWire REST API."""

    def __init__(self, config: SignalWireConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        """Send an SMS to every configured recipient."""
        if not self._config.to_numbers:
            return

        cfg = self._config
        base_url = (
            f"https://{cfg.space_url}/api/laml/2010-04-01"
            f"/Accounts/{cfg.project_id}/Messages.json"
        )
        body = payload.summary()

        for number in cfg.to_numbers:
            response = requests.post(
                base_url,
                data={
                    "From": cfg.from_number,
                    "To": number,
                    "Body": body,
                },
                auth=(cfg.project_id, cfg.api_token),
                timeout=10,
            )
            response.raise_for_status()
