from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.rocketchat_notifier import RocketChatConfig, RocketChatNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> RocketChatConfig:
    return RocketChatConfig(
        webhook_url="https://chat.example.com/hooks/abc123",
        channel="#alerts",
        username="cronwatch-bot",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 15, 2, 0, 0),
        expected_at=_utc(2024, 1, 15, 3, 0, 0),
        failure_count=0,
    )


@pytest.fixture()
def _mock_response() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    return resp


def test_send_posts_to_webhook(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        notifier = RocketChatNotifier(config)
        notifier.send(payload)

    mock_post.assert_called_once()
    url, *_ = mock_post.call_args.args
    assert url == config.webhook_url


def test_message_contains_job_name(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        RocketChatNotifier(config).send(payload)

    body = mock_post.call_args.kwargs["json"]
    assert "nightly-backup" in body["text"]


def test_channel_included_when_set(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        RocketChatNotifier(config).send(payload)

    body = mock_post.call_args.kwargs["json"]
    assert body["channel"] == "#alerts"


def test_channel_omitted_when_empty(payload, _mock_response):
    cfg = RocketChatConfig(webhook_url="https://chat.example.com/hooks/xyz")
    with patch("requests.post", return_value=_mock_response) as mock_post:
        RocketChatNotifier(cfg).send(payload)

    body = mock_post.call_args.kwargs["json"]
    assert "channel" not in body


def test_http_error_propagates(config, payload):
    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = Exception("HTTP 500")
    with patch("requests.post", return_value=error_resp):
        with pytest.raises(Exception, match="HTTP 500"):
            RocketChatNotifier(config).send(payload)


def test_empty_webhook_url_raises():
    with pytest.raises(ValueError, match="webhook_url"):
        RocketChatConfig(webhook_url="")
