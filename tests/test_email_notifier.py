"""Tests for EmailNotifier."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.email_notifier import EmailConfig, EmailNotifier


def _utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 3),
        expected_at=_utc(2024, 1, 10, 4),
    )


@pytest.fixture()
def config() -> EmailConfig:
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        use_tls=True,
        username="user@example.com",
        password="secret",
        sender="alerts@example.com",
        recipients=["ops@example.com"],
    )


def test_send_calls_smtp(payload: AlertPayload, config: EmailConfig) -> None:
    notifier = EmailNotifier(config)
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        notifier.send(payload)

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with(config.username, config.password)
    mock_server.sendmail.assert_called_once()
    args = mock_server.sendmail.call_args[0]
    assert args[0] == config.sender
    assert args[1] == config.recipients
    assert "backup" in args[2]


def test_no_send_when_no_recipients(payload: AlertPayload, config: EmailConfig) -> None:
    config.recipients = []
    notifier = EmailNotifier(config)
    with patch("smtplib.SMTP") as mock_smtp_cls:
        notifier.send(payload)
        mock_smtp_cls.assert_not_called()


def test_smtp_exception_is_raised(payload: AlertPayload, config: EmailConfig) -> None:
    notifier = EmailNotifier(config)
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.side_effect = smtplib.SMTPException("conn failed")
        with pytest.raises(smtplib.SMTPException):
            notifier.send(payload)


def test_subject_contains_job_name(payload: AlertPayload, config: EmailConfig) -> None:
    notifier = EmailNotifier(config)
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        notifier.send(payload)

    raw_message = mock_server.sendmail.call_args[0][2]
    assert "backup" in raw_message
    assert "cronwatch" in raw_message
