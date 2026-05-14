"""SMS notifier via Twilio REST API."""
from __future__ import annotations

import urllib.request
import urllib.parse
import base64
import json
from dataclasses import dataclass, field
from typing import List

from .base import AlertPayload, BaseNotifier


@dataclass
class SMSConfig:
    """Twilio credentials and targeting."""

    account_sid: str
    auth_token: str
    from_number: str  # E.164 format, e.g. "+15550001234"
    to_numbers: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.account_sid:
            raise ValueError("account_sid must not be empty")
        if not self.auth_token:
            raise ValueError("auth_token must not be empty")
        if not self.from_number:
            raise ValueError("from_number must not be empty")


class SMSNotifier(BaseNotifier):
    """Send alert SMS messages via Twilio."""

    _BASE_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

    def __init__(self, config: SMSConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        """Send an SMS to every configured recipient."""
        if not self.config.to_numbers:
            return

        url = self._BASE_URL.format(sid=self.config.account_sid)
        credentials = base64.b64encode(
            f"{self.config.account_sid}:{self.config.auth_token}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = payload.summary()

        for number in self.config.to_numbers:
            data = urllib.parse.urlencode(
                {"From": self.config.from_number, "To": number, "Body": body}
            ).encode()
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 201):
                    raw = resp.read().decode()
                    raise RuntimeError(
                        f"Twilio returned {resp.status} for {number}: {raw}"
                    )
