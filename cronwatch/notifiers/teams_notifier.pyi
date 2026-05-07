"""Type stubs for teams_notifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

@dataclass
class TeamsConfig:
    webhook_url: str
    timeout: int = ...
    mention_emails: List[str] = ...

class TeamsNotifier(BaseNotifier):
    config: TeamsConfig
    def __init__(self, config: TeamsConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_message(self, payload: AlertPayload) -> dict: ...
