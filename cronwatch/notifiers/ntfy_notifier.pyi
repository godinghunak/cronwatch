from typing import Optional
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class NtfyConfig:
    topic: str
    server: str
    token: Optional[str]
    priority: str
    tags: list[str]
    timeout: int

    def __init__(
        self,
        topic: str,
        server: str = ...,
        token: Optional[str] = ...,
        priority: str = ...,
        tags: list[str] = ...,
        timeout: int = ...,
    ) -> None: ...
    def __post_init__(self) -> None: ...

class NtfyNotifier(BaseNotifier):
    config: NtfyConfig

    def __init__(self, config: NtfyConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
