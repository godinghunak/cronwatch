"""Matrix notifier — sends alerts to a Matrix room via the Client-Server API."""

from __future__ import annotations

import urllib.request
import urllib.error
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class MatrixConfig:
    homeserver_url: str  # e.g. "https://matrix.example.com"
    access_token: str
    room_id: str          # e.g. "!roomid:example.com"
    timeout: int = 10
    extra_headers: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.homeserver_url.startswith(("http://", "https://")):
            raise ValueError("homeserver_url must start with http:// or https://")
        if not self.room_id:
            raise ValueError("room_id must not be empty")
        if not self.access_token:
            raise ValueError("access_token must not be empty")


class MatrixNotifier(BaseNotifier):
    """Sends a plain-text message to a Matrix room."""

    def __init__(self, config: MatrixConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self._config
        url = (
            f"{cfg.homeserver_url.rstrip('/')}/_matrix/client/v3/rooms/"
            f"{urllib.request.quote(cfg.room_id, safe='')}/send/m.room.message"
        )
        body = self._build_message(payload)
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.access_token}",
                **cfg.extra_headers,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
                status = resp.status
            logger.debug("Matrix notifier: room=%s status=%s", cfg.room_id, status)
        except urllib.error.HTTPError as exc:
            logger.error("Matrix notifier HTTP error %s: %s", exc.code, exc.reason)
        except Exception as exc:  # noqa: BLE001
            logger.error("Matrix notifier error: %s", exc)

    def _build_message(self, payload: AlertPayload) -> dict:
        return {
            "msgtype": "m.text",
            "body": payload.summary(),
        }
