# Zulip Notifier

Send cronwatch alerts to a [Zulip](https://zulip.com/) stream using a bot.

## Prerequisites

1. Create a bot in your Zulip organisation (**Settings → Bots → Add a new bot**).
2. Note the bot's **email** and **API key**.
3. Subscribe the bot to the target stream.

## Configuration

```python
from cronwatch.notifiers.zulip_notifier import ZulipConfig, ZulipNotifier

config = ZulipConfig(
    site_url="https://yourorg.zulipchat.com",
    bot_email="cronwatch-bot@yourorg.zulipchat.com",
    bot_api_key="your-bot-api-key",
    stream="ops-alerts",
    topic="cronwatch",   # optional, default: "cronwatch alerts"
    timeout=10,          # optional, default: 10
)

notifier = ZulipNotifier(config)
```

## Usage with CronChecker

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry=registry, notifiers=[notifier])
checker.check_all()
```

## Parameters

| Parameter     | Type  | Required | Description                              |
|---------------|-------|----------|------------------------------------------|
| `site_url`    | `str` | Yes      | Base URL of your Zulip instance          |
| `bot_email`   | `str` | Yes      | Email address of the Zulip bot           |
| `bot_api_key` | `str` | Yes      | API key for the bot                      |
| `stream`      | `str` | Yes      | Stream name to post messages into        |
| `topic`       | `str` | No       | Topic within the stream (default shown)  |
| `timeout`     | `int` | No       | HTTP request timeout in seconds          |

## Alert format

Messages are posted as plain text using the standard `AlertPayload.summary()` format:

```
[cronwatch] ALERT — backup: missed schedule (last seen: 2024-01-01 10:00:00 UTC, expected: 2024-01-01 11:00:00 UTC)
```
