"""Tests for GotifyNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.gotify_notifier import GotifyConfig, GotifyNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> GotifyConfig:
    return GotifyConfig(
        server_url="https://gotify.example.com/",
        app_token="test-token-abc",
        priority=7,
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


def test_send_posts_to_correct_url(config, payload, _mock_response):
    with patch("cronwatch.notifiers.gotify_notifier.requests.post", return_value=_mock_response) as mock_post:
        GotifyNotifier(config).send(payload)

    mock_post.assert_called_once()
    url = mock_post.call_args.args[0]
    assert url == "https://gotify.example.com/message"


def test_send_uses_app_token_header(config, payload, _mock_response):
    with patch("cronwatch.notifiers.gotify_notifier.requests.post", return_value=_mock_response) as mock_post:
        GotifyNotifier(config).send(payload)

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["X-Gotify-Key"] == "test-token-abc"


def test_message_body_contains_job_name(config, payload, _mock_response):
    with patch("cronwatch.notifiers.gotify_notifier.requests.post", return_value=_mock_response) as mock_post:
        GotifyNotifier(config).send(payload)

    body = mock_post.call_args.kwargs["json"]
    assert "nightly-backup" in body["title"]
    assert "nightly-backup" in body["message"]


def test_priority_is_forwarded(config, payload, _mock_response):
    with patch("cronwatch.notifiers.gotify_notifier.requests.post", return_value=_mock_response) as mock_post:
        GotifyNotifier(config).send(payload)

    body = mock_post.call_args.kwargs["json"]
    assert body["priority"] == 7


def test_trailing_slash_stripped_from_url():
    cfg = GotifyConfig(server_url="https://gotify.example.com/", app_token="tok")
    assert cfg.server_url == "https://gotify.example.com"


def test_empty_server_url_raises():
    with pytest.raises(ValueError, match="server_url"):
        GotifyConfig(server_url="", app_token="tok")


def test_empty_app_token_raises():
    with pytest.raises(ValueError, match="app_token"):
        GotifyConfig(server_url="https://gotify.example.com", app_token="")


def test_extra_headers_merged(payload, _mock_response):
    cfg = GotifyConfig(
        server_url="https://gotify.example.com",
        app_token="tok",
        extra_headers={"X-Custom": "value"},
    )
    with patch("cronwatch.notifiers.gotify_notifier.requests.post", return_value=_mock_response) as mock_post:
        GotifyNotifier(cfg).send(payload)

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["X-Custom"] == "value"
    assert headers["X-Gotify-Key"] == "tok"
