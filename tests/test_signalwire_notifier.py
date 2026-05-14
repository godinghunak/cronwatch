"""Tests for the SignalWire SMS notifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.signalwire_notifier import SignalWireConfig, SignalWireNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def config() -> SignalWireConfig:
    return SignalWireConfig(
        space_url="example.signalwire.com",
        project_id="proj-abc123",
        api_token="tok-secret",
        from_number="+15550001111",
        to_numbers=["+15559990000", "+15558880000"],
    )


@pytest.fixture
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 8, 0, 0),
        expected_at=_utc(2024, 1, 10, 9, 0, 0),
    )


@pytest.fixture
def _mock_response() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    return resp


def test_send_posts_to_each_number(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        notifier = SignalWireNotifier(config)
        notifier.send(payload)

    assert mock_post.call_count == 2
    urls = [call.args[0] for call in mock_post.call_args_list]
    for url in urls:
        assert "proj-abc123" in url
        assert "example.signalwire.com" in url


def test_send_uses_correct_auth(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        SignalWireNotifier(config).send(payload)

    for call in mock_post.call_args_list:
        assert call.kwargs["auth"] == ("proj-abc123", "tok-secret")


def test_send_includes_body(config, payload, _mock_response):
    with patch("requests.post", return_value=_mock_response) as mock_post:
        SignalWireNotifier(config).send(payload)

    for call in mock_post.call_args_list:
        body = call.kwargs["data"]["Body"]
        assert "backup-job" in body
        assert "missed schedule" in body


def test_no_send_when_no_recipients(payload, _mock_response):
    cfg = SignalWireConfig(
        space_url="example.signalwire.com",
        project_id="proj-abc123",
        api_token="tok-secret",
        from_number="+15550001111",
        to_numbers=[],
    )
    with patch("requests.post", return_value=_mock_response) as mock_post:
        SignalWireNotifier(cfg).send(payload)

    mock_post.assert_not_called()


def test_http_error_propagates(config, payload):
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")

    with patch("requests.post", return_value=error_response):
        with pytest.raises(requests.HTTPError):
            SignalWireNotifier(config).send(payload)


def test_invalid_config_raises():
    with pytest.raises(ValueError, match="space_url"):
        SignalWireConfig(
            space_url="",
            project_id="proj",
            api_token="tok",
            from_number="+1555",
        )
