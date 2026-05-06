"""Tests for cronwatch.scheduler."""

from datetime import datetime, timezone

import pytest

from cronwatch.scheduler import CronSchedule


DEFAULT_JOB = "test_job"


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_invalid_expression_raises():
    with pytest.raises(ValueError, match="Invalid cron expression"):
        CronSchedule("not-a-cron", DEFAULT_JOB)


def test_last_expected_run_is_before_reference():
    sched = CronSchedule("0 * * * *", DEFAULT_JOB)  # every hour
    ref = _utc(2024, 1, 15, 14, 30)  # 14:30
    last = sched.last_expected_run(ref)
    assert last < ref
    assert last.minute == 0
    assert last.hour == 14


def test_next_expected_run_is_after_reference():
    sched = CronSchedule("0 * * * *", DEFAULT_JOB)
    ref = _utc(2024, 1, 15, 14, 30)
    nxt = sched.next_expected_run(ref)
    assert nxt > ref
    assert nxt.hour == 15


def test_is_missed_when_last_seen_is_old():
    sched = CronSchedule("0 * * * *", DEFAULT_JOB)
    ref = _utc(2024, 1, 15, 14, 30)
    # Simulate last_seen two hours before reference
    last_seen = _utc(2024, 1, 15, 12, 0)
    assert sched.is_missed(last_seen, tolerance_seconds=60) is True


def test_is_not_missed_when_last_seen_is_recent():
    sched = CronSchedule("0 * * * *", DEFAULT_JOB)
    # last_seen just one minute after the last expected hour mark
    ref = _utc(2024, 1, 15, 14, 30)
    last_seen = _utc(2024, 1, 15, 14, 1)  # ran at 14:01, expected was 14:00
    assert sched.is_missed(last_seen, tolerance_seconds=120) is False
