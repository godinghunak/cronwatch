"""Type stubs for telegram_notifier."""

from dataclasses import dataclass, field
from typing import List

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

@dataclass
class TelegramConfig:
    bot_token: str
    chat_ids: List[str]
    parse_mode: str
    timeout: int

class TelegramNotifier(BaseNotifier):
    def __init__(self, config: TelegramConfig) -> None: ...
    def send(self, payload: AlertPayload) -> None: ...
    def _build_message(self, payload: AlertPayload) -> str: ...
    def _post(self, chat_id: str, text: str) -> None: ...
