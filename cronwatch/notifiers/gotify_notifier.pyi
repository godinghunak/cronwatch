from dataclasses import dataclass, field
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

@dataclass
class GotifyConfig:
    server_url: str
    app_token: str
    priority: int
    timeout: int
    extra_headers: dict
    def __post_init__(self) -> None: ...

class GotifyNotifier(BaseNotifier):
    def __init__(self, config: GotifyConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_message(self, payload: AlertPayload) -> dict: ...
