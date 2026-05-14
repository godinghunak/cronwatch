from typing import Any
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class RocketChatConfig:
    webhook_url: str
    channel: str
    username: str
    icon_emoji: str
    timeout: int
    extra_fields: dict[str, Any]

    def __init__(
        self,
        webhook_url: str,
        channel: str = ...,
        username: str = ...,
        icon_emoji: str = ...,
        timeout: int = ...,
        extra_fields: dict[str, Any] = ...,
    ) -> None: ...

class RocketChatNotifier(BaseNotifier):
    config: RocketChatConfig

    def __init__(self, config: RocketChatConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_message(self, payload: AlertPayload) -> dict[str, Any]: ...
