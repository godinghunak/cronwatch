"""Tests for the Pushover notifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.pushover_notifier import PushoverConfig, PushoverNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> PushoverConfig:
    return PushoverConfig(
        api_token="tok_abc123",
        user_keys=["user_key_1", "user_key_2"],
        priority=0,
        sound="falling",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 2, 0, 0),
        expected_at=_utc(2024, 1, 10, 3, 0, 0),
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


def test_send_posts_to_each_user_key(config, payload):
    with patch("cronwatch.notifiers.pushover_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        notifier = PushoverNotifier(config)
        notifier.send(payload)

    assert mock_post.call_count == 2
    urls = [call.args[0] for call in mock_post.call_args_list]
    assert all("pushover.net" in u for u in urls)


def test_send_includes_api_token(config, payload):
    with patch("cronwatch.notifiers.pushover_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        PushoverNotifier(config).send(payload)

    body = mock_post.call_args_list[0].kwargs["data"]
    assert body["token"] == "tok_abc123"


def test_send_includes_summary_in_message(config, payload):
    with patch("cronwatch.notifiers.pushover_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        PushoverNotifier(config).send(payload)

    body = mock_post.call_args_list[0].kwargs["data"]
    assert "nightly-backup" in body["message"]
    assert "missed schedule" in body["message"]


def test_no_send_when_no_user_keys(payload):
    cfg = PushoverConfig(api_token="tok", user_keys=[])
    with patch("cronwatch.notifiers.pushover_notifier.requests.post") as mock_post:
        PushoverNotifier(cfg).send(payload)
    mock_post.assert_not_called()


def test_invalid_priority_raises():
    with pytest.raises(ValueError, match="priority"):
        PushoverConfig(api_token="tok", user_keys=["u1"], priority=3)


def test_raises_on_http_error(config, payload):
    bad_resp = _mock_response(500)
    bad_resp.raise_for_status.side_effect = Exception("HTTP 500")
    with patch("cronwatch.notifiers.pushover_notifier.requests.post", return_value=bad_resp):
        with pytest.raises(Exception, match="HTTP 500"):
            PushoverNotifier(config).send(payload)
