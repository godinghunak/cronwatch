# Linear Notifier

The `LinearNotifier` creates a [Linear](https://linear.app) issue whenever a cronwatch alert fires.

## Installation

No extra dependencies are required beyond `requests`, which is already a cronwatch dependency.

## Configuration

```python
from cronwatch.notifiers.linear_notifier import LinearConfig, LinearNotifier

config = LinearConfig(
    api_key="lin_api_xxxxxxxxxxxx",  # Linear personal or service API key
    team_id="TEAM-UUID",             # Target team UUID
    assignee_id="USER-UUID",         # Optional: auto-assign the issue
    priority=2,                      # 1=urgent 2=high 3=medium 4=low (default: 2)
    label_ids=["LABEL-UUID"],        # Optional: attach labels
)

notifier = LinearNotifier(config)
```

## Usage with CronChecker

```python
from cronwatch.checker import CronChecker
from cronwatch.job_registry import JobRegistry
from cronwatch.notifiers.linear_notifier import LinearConfig, LinearNotifier

registry = JobRegistry()
config = LinearConfig(api_key="lin_api_xxx", team_id="TEAM-UUID")
checker = CronChecker(registry=registry, notifiers=[LinearNotifier(config)])
checker.check_all()
```

## Issue Format

Each created issue has:

- **Title:** `[cronwatch] <job_name>: <reason>`
- **Description:** job name, reason, last success/failure timestamps, and a summary line.
- **Priority:** configurable (default: high).

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `api_key` | `str` | ✅ | Linear API key |
| `team_id` | `str` | ✅ | Linear team UUID |
| `assignee_id` | `str` | ❌ | User UUID to assign |
| `priority` | `int` | ❌ | 1–4, default `2` |
| `label_ids` | `list[str]` | ❌ | Label UUIDs to attach |
