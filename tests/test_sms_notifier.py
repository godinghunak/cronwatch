"""Tests for SMSNotifier."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.sms_notifier import SMSConfig, SMSNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> SMSConfig:
    return SMSConfig(
        account_sid="ACtest123",
        auth_token="secret",
        from_number="+15550001111",
        to_numbers=["+15550002222", "+15550003333"],
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 1, 9, 0, 0),
        expected_at=_utc(2024, 1, 1, 10, 0, 0),
    )


def _mock_response(status: int = 201) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_posts_to_each_number(config: SMSConfig, payload: AlertPayload) -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        SMSNotifier(config).send(payload)
    assert mock_open.call_count == 2


def test_no_send_when_no_recipients(payload: AlertPayload) -> None:
    cfg = SMSConfig(
        account_sid="ACtest", auth_token="tok", from_number="+1555", to_numbers=[]
    )
    with patch("urllib.request.urlopen") as mock_open:
        SMSNotifier(cfg).send(payload)
    mock_open.assert_not_called()


def test_request_contains_body(config: SMSConfig, payload: AlertPayload) -> None:
    captured: list = []

    def fake_urlopen(req):
        captured.append(req)
        return _mock_response()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        SMSNotifier(config).send(payload)

    assert captured
    body = captured[0].data.decode()
    assert "backup" in body
    assert "%2B15550002222" in body or "15550002222" in body


def test_raises_on_bad_status(config: SMSConfig, payload: AlertPayload) -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(status=400)):
        with pytest.raises(RuntimeError, match="Twilio returned 400"):
            SMSNotifier(config).send(payload)


def test_invalid_config_raises() -> None:
    with pytest.raises(ValueError, match="account_sid"):
        SMSConfig(account_sid="", auth_token="t", from_number="+1")


def test_authorization_header_is_basic(config: SMSConfig, payload: AlertPayload) -> None:
    captured: list = []

    def fake_urlopen(req):
        captured.append(req)
        return _mock_response()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        SMSNotifier(config).send(payload)

    auth = captured[0].get_header("Authorization")
    assert auth.startswith("Basic ")
