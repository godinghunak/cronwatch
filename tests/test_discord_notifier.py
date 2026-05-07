from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.discord_notifier import DiscordConfig, DiscordNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> DiscordConfig:
    return DiscordConfig(webhook_url="https://discord.com/api/webhooks/test/token")


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 8, 0, 0),
        alert_time=_utc(2024, 1, 10, 9, 0, 0),
    )


def _mock_response(status_code: int = 204) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


def test_send_posts_to_webhook(config, payload):
    with patch("cronwatch.notifiers.discord_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(204)
        notifier = DiscordNotifier(config)
        notifier.send(payload)

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert call_kwargs[0][0] == config.webhook_url
    body = call_kwargs[1]["json"]
    assert body["username"] == "CronWatch"
    assert "backup-job" in body["content"]
    assert "missed schedule" in body["content"]


def test_message_contains_mentions(payload):
    cfg = DiscordConfig(
        webhook_url="https://discord.com/api/webhooks/x/y",
        mentions=["<@&111>", "<@222>"],
    )
    with patch("cronwatch.notifiers.discord_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(204)
        notifier = DiscordNotifier(cfg)
        notifier.send(payload)

    body = mock_post.call_args[1]["json"]
    assert "<@&111>" in body["content"]
    assert "<@222>" in body["content"]


def test_avatar_url_included_when_set(payload):
    cfg = DiscordConfig(
        webhook_url="https://discord.com/api/webhooks/x/y",
        avatar_url="https://example.com/avatar.png",
    )
    with patch("cronwatch.notifiers.discord_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(204)
        DiscordNotifier(cfg).send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["avatar_url"] == "https://example.com/avatar.png"


def test_no_avatar_url_when_not_set(config, payload):
    with patch("cronwatch.notifiers.discord_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(204)
        DiscordNotifier(config).send(payload)

    body = mock_post.call_args[1]["json"]
    assert "avatar_url" not in body


def test_http_error_is_logged_not_raised(config, payload):
    with patch("cronwatch.notifiers.discord_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(400)
        notifier = DiscordNotifier(config)
        # Should not raise even when Discord returns an error
        notifier.send(payload)
