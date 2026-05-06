"""Tests for cronwatch.checker."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.checker import CronChecker
from cronwatch.job_registry import JobRegistry


def _make_registry_with_job(cron: str = "0 * * * *") -> JobRegistry:
    reg = JobRegistry()
    reg.register("backup", cron)
    return reg


def test_no_alert_when_heartbeat_is_recent():
    registry = _make_registry_with_job()
    # Record a heartbeat right now
    registry.heartbeat("backup")

    callback = MagicMock()
    checker = CronChecker(registry, [callback], tolerance_seconds=3600)

    with patch("cronwatch.scheduler.CronSchedule.is_missed", return_value=False):
        checker.check_all()

    callback.assert_not_called()


def test_alert_fired_when_job_never_ran():
    registry = _make_registry_with_job()
    callback = MagicMock()
    checker = CronChecker(registry, [callback])
    checker.check_all()

    callback.assert_called_once()
    job_name, message = callback.call_args[0]
    assert job_name == "backup"
    assert "never reported" in message


def test_alert_fired_on_failure_threshold():
    registry = _make_registry_with_job()
    registry.record_failure("backup", "exit code 1")
    callback = MagicMock()
    checker = CronChecker(registry, [callback], failure_threshold=1)
    checker.check_all()

    callback.assert_called_once()
    _, message = callback.call_args[0]
    assert "failed" in message
    assert "exit code 1" in message


def test_alert_fired_on_missed_schedule():
    registry = _make_registry_with_job()
    old_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
    registry.heartbeat("backup")
    registry.get("backup").last_seen = old_time

    callback = MagicMock()
    checker = CronChecker(registry, [callback], tolerance_seconds=60)
    checker.check_all()

    callback.assert_called_once()
    _, message = callback.call_args[0]
    assert "missed" in message


def test_callback_exception_does_not_propagate():
    registry = _make_registry_with_job()
    bad_callback = MagicMock(side_effect=RuntimeError("boom"))
    checker = CronChecker(registry, [bad_callback])
    # Should not raise even if callback blows up
    checker.check_all()
