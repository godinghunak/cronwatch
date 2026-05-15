"""Tests for ClickUpNotifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.clickup_notifier import ClickUpConfig, ClickUpNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> ClickUpConfig:
    return ClickUpConfig(
        api_token="pk_test_token",
        list_id="99887766",
        tags=["cronwatch", "alert"],
        priority=2,
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly_backup",
        reason="missed schedule",
        last_seen=_utc(2024, 6, 1, 2, 0, 0),
        expected_at=_utc(2024, 6, 1, 3, 0, 0),
        exit_code=None,
    )


def _mock_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {"id": "task_abc123"}
    resp.raise_for_status = MagicMock()
    return resp


def test_send_creates_task(config: ClickUpConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.clickup_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        ClickUpNotifier(config).send(payload)

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["name"] == "[cronwatch] nightly_backup: missed schedule"
    assert kwargs["json"]["priority"] == 2
    assert "cronwatch" in kwargs["json"]["tags"]


def test_send_includes_summary_in_description(config: ClickUpConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.clickup_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        ClickUpNotifier(config).send(payload)

    body = mock_post.call_args[1]["json"]
    assert "nightly_backup" in body["description"]
    assert "missed schedule" in body["description"]


def test_send_uses_correct_list_url(config: ClickUpConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.clickup_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        ClickUpNotifier(config).send(payload)

    url = mock_post.call_args[0][0]
    assert "99887766" in url
    assert url.endswith("/task")


def test_send_swallows_request_exception(config: ClickUpConfig, payload: AlertPayload) -> None:
    import requests as req

    with patch("cronwatch.notifiers.clickup_notifier.requests.post", side_effect=req.ConnectionError("timeout")):
        # Should not raise
        ClickUpNotifier(config).send(payload)


def test_no_tags_when_empty(payload: AlertPayload) -> None:
    cfg = ClickUpConfig(api_token="pk_test", list_id="123", tags=[])
    with patch("cronwatch.notifiers.clickup_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        ClickUpNotifier(cfg).send(payload)

    body = mock_post.call_args[1]["json"]
    assert "tags" not in body


def test_invalid_priority_raises() -> None:
    with pytest.raises(ValueError, match="priority"):
        ClickUpConfig(api_token="pk_test", list_id="123", priority=5)


def test_empty_api_token_raises() -> None:
    with pytest.raises(ValueError, match="api_token"):
        ClickUpConfig(api_token="", list_id="123")
