"""Tests for MattermostNotifier."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.mattermost_notifier import MattermostConfig, MattermostNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> MattermostConfig:
    return MattermostConfig(
        webhook_url="https://mattermost.example.com/hooks/abc123",
        channel="#ops-alerts",
        username="cronwatch-bot",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 15, 3, 0, 0),
    )


def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_posts_to_webhook(config, payload):
    notifier = MattermostNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)

    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    assert req.full_url == config.webhook_url
    assert req.method == "POST"
    body = json.loads(req.data)
    assert "nightly-backup" in body["text"]
    assert "missed schedule" in body["text"]


def test_channel_included_when_set(config, payload):
    notifier = MattermostNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        notifier.send(payload)

    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data)
    assert body["channel"] == "#ops-alerts"


def test_no_channel_key_when_not_set(payload):
    cfg = MattermostConfig(webhook_url="https://mattermost.example.com/hooks/xyz")
    notifier = MattermostNotifier(cfg)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data)
    assert "channel" not in body


def test_username_in_payload(config, payload):
    notifier = MattermostNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data)
    assert body["username"] == "cronwatch-bot"


def test_url_error_logs_warning(config, payload, caplog):
    import urllib.error

    notifier = MattermostNotifier(config)
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        with caplog.at_level("ERROR"):
            notifier.send(payload)  # should not raise
    assert "Failed to send Mattermost alert" in caplog.text


def test_last_seen_appears_in_message(config, payload):
    notifier = MattermostNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data)
    assert "2024-01-15" in body["text"]
