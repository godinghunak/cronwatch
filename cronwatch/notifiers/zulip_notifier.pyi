from dataclasses import dataclass
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

@dataclass
class ZulipConfig:
    site_url: str
    bot_email: str
    bot_api_key: str
    stream: str
    topic: str
    timeout: int
    def __post_init__(self) -> None: ...

class ZulipNotifier(BaseNotifier):
    def __init__(self, config: ZulipConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_message(self, payload: AlertPayload) -> dict: ...
