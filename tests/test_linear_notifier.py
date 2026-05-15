"""Tests for LinearNotifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.linear_notifier import LinearConfig, LinearNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> LinearConfig:
    return LinearConfig(
        api_key="lin_api_test123",
        team_id="TEAM-001",
        assignee_id="USER-42",
        priority=2,
        label_ids=["LABEL-1"],
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_success=_utc(2024, 1, 10, 2, 0, 0),
        last_failure=None,
    )


def _mock_response(success: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "data": {
            "issueCreate": {
                "success": success,
                "issue": {
                    "id": "ISS-99",
                    "title": "[cronwatch] nightly-backup: missed schedule",
                    "url": "https://linear.app/team/issue/ISS-99",
                },
            }
        }
    }
    resp.raise_for_status = MagicMock()
    return resp


def test_send_creates_linear_issue(config: LinearConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.linear_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        LinearNotifier(config).send(payload)

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    body = kwargs["json"]
    assert "issueCreate" in body["query"]
    inp = body["variables"]["input"]
    assert inp["teamId"] == "TEAM-001"
    assert "nightly-backup" in inp["title"]
    assert inp["priority"] == 2
    assert inp["assigneeId"] == "USER-42"
    assert inp["labelIds"] == ["LABEL-1"]


def test_send_uses_correct_auth_header(config: LinearConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.linear_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response()
        LinearNotifier(config).send(payload)

    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == "lin_api_test123"


def test_send_logs_error_on_api_failure(
    config: LinearConfig, payload: AlertPayload, caplog: pytest.LogCaptureFixture
) -> None:
    with patch("cronwatch.notifiers.linear_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(success=False)
        import logging
        with caplog.at_level(logging.ERROR, logger="cronwatch.notifiers.linear_notifier"):
            LinearNotifier(config).send(payload)

    assert any("failed" in r.message.lower() for r in caplog.records)


def test_config_rejects_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        LinearConfig(api_key="", team_id="TEAM-001")


def test_config_rejects_empty_team_id() -> None:
    with pytest.raises(ValueError, match="team_id"):
        LinearConfig(api_key="lin_api_key", team_id="")


def test_config_rejects_invalid_priority() -> None:
    with pytest.raises(ValueError, match="priority"):
        LinearConfig(api_key="lin_api_key", team_id="TEAM-001", priority=5)


def test_description_contains_job_name(config: LinearConfig, payload: AlertPayload) -> None:
    notifier = LinearNotifier(config)
    desc = notifier._build_description(payload)
    assert "nightly-backup" in desc
    assert "missed schedule" in desc
    assert "2024-01-10" in desc
