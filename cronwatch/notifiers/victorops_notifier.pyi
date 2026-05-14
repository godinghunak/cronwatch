from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class VictorOpsConfig:
    routing_key: str
    rest_endpoint_url: str
    message_type: str
    timeout: int
    def __init__(
        self,
        routing_key: str,
        rest_endpoint_url: str,
        message_type: str = ...,
        timeout: int = ...,
    ) -> None: ...

class VictorOpsNotifier(BaseNotifier):
    config: VictorOpsConfig
    def __init__(self, config: VictorOpsConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_event(self, payload: AlertPayload) -> dict: ...
