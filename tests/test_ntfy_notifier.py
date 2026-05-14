"""Tests for the ntfy notifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.ntfy_notifier import NtfyConfig, NtfyNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def config() -> NtfyConfig:
    return NtfyConfig(topic="cronwatch-alerts", server="https://ntfy.sh")


@pytest.fixture
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 8, 0, 0),
        expected_at=_utc(2024, 1, 10, 9, 0, 0),
        failure_count=0,
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock(
        side_effect=None if status_code < 400 else Exception("HTTP error")
    )
    return resp


def test_send_posts_to_correct_url(config: NtfyConfig, payload: AlertPayload) -> None:
    notifier = NtfyNotifier(config)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert call_url == "https://ntfy.sh/cronwatch-alerts"


def test_send_includes_job_name_in_title(config: NtfyConfig, payload: AlertPayload) -> None:
    notifier = NtfyNotifier(config)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    headers = mock_post.call_args[1]["headers"]
    assert "backup-job" in headers["Title"]
    assert "missed schedule" in headers["Title"]


def test_send_includes_bearer_token_when_configured(payload: AlertPayload) -> None:
    cfg = NtfyConfig(topic="secure-topic", token="secret-token-123")
    notifier = NtfyNotifier(cfg)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer secret-token-123"


def test_no_auth_header_when_token_is_none(config: NtfyConfig, payload: AlertPayload) -> None:
    notifier = NtfyNotifier(config)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    headers = mock_post.call_args[1]["headers"]
    assert "Authorization" not in headers


def test_raises_on_http_error(config: NtfyConfig, payload: AlertPayload) -> None:
    notifier = NtfyNotifier(config)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(500)
        mock_post.return_value.raise_for_status.side_effect = Exception("Server error")
        with pytest.raises(Exception, match="Server error"):
            notifier.send(payload)


def test_invalid_priority_raises() -> None:
    with pytest.raises(ValueError, match="priority"):
        NtfyConfig(topic="alerts", priority="extreme")


def test_empty_topic_raises() -> None:
    with pytest.raises(ValueError, match="topic"):
        NtfyConfig(topic="")


def test_custom_server_url_used(payload: AlertPayload) -> None:
    cfg = NtfyConfig(topic="my-topic", server="https://ntfy.example.com")
    notifier = NtfyNotifier(cfg)
    with patch("cronwatch.notifiers.ntfy_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    call_url = mock_post.call_args[0][0]
    assert call_url == "https://ntfy.example.com/my-topic"
