"""Tests for MatrixNotifier."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.matrix_notifier import MatrixConfig, MatrixNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def config() -> MatrixConfig:
    return MatrixConfig(
        homeserver_url="https://matrix.example.com",
        access_token="syt_test_token",
        room_id="!abc123:example.com",
    )


@pytest.fixture
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 15, 10, 0, 0),
        expected_at=_utc(2024, 1, 15, 11, 0, 0),
    )


def _mock_response(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_posts_to_correct_url(config, payload):
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        MatrixNotifier(config).send(payload)
    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    assert "/_matrix/client/v3/rooms/" in req.full_url
    assert "/send/m.room.message" in req.full_url


def test_send_includes_bearer_token(config, payload):
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        MatrixNotifier(config).send(payload)
    req = mock_open.call_args[0][0]
    assert req.get_header("Authorization") == "Bearer syt_test_token"


def test_send_body_contains_summary(config, payload):
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        MatrixNotifier(config).send(payload)
    req = mock_open.call_args[0][0]
    body = json.loads(req.data)
    assert "backup-job" in body["body"]
    assert body["msgtype"] == "m.text"


def test_http_error_is_logged_not_raised(config, payload):
    import urllib.error
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(None, 403, "Forbidden", {}, None),
    ):
        MatrixNotifier(config).send(payload)  # must not raise


def test_generic_error_is_logged_not_raised(config, payload):
    with patch("urllib.request.urlopen", side_effect=ConnectionError("refused")):
        MatrixNotifier(config).send(payload)  # must not raise


def test_invalid_homeserver_url_raises():
    with pytest.raises(ValueError, match="homeserver_url"):
        MatrixConfig(
            homeserver_url="matrix.example.com",
            access_token="tok",
            room_id="!x:example.com",
        )


def test_empty_room_id_raises():
    with pytest.raises(ValueError, match="room_id"):
        MatrixConfig(
            homeserver_url="https://matrix.example.com",
            access_token="tok",
            room_id="",
        )
