from typing import List
from .base import AlertPayload, BaseNotifier

class SMSConfig:
    account_sid: str
    auth_token: str
    from_number: str
    to_numbers: List[str]
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str] = ...,
    ) -> None: ...

class SMSNotifier(BaseNotifier):
    config: SMSConfig
    def __init__(self, config: SMSConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
