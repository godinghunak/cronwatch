from dataclasses import dataclass
from typing import List

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

PUSHOVER_API_URL: str

@dataclass
class PushoverConfig:
    api_token: str
    user_keys: List[str]
    priority: int
    sound: str
    timeout: int
    def __post_init__(self) -> None: ...

class PushoverNotifier(BaseNotifier):
    def __init__(self, config: PushoverConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_body(self, user_key: str, title: str, message: str) -> dict: ...
