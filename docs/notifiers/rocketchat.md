# Rocket.Chat Notifier

Send cronwatch alerts to a [Rocket.Chat](https://rocket.chat/) channel using an
[incoming webhook](https://docs.rocket.chat/use-rocket.chat/workspace-administration/integrations/incoming-webhooks-scripting).

## Setup

1. In Rocket.Chat, go to **Administration → Integrations → New Integration → Incoming WebHook**.
2. Choose a channel, give it a name, and save.
3. Copy the generated **Webhook URL**.

## Configuration

```python
from cronwatch.notifiers.rocketchat_notifier import RocketChatConfig, RocketChatNotifier

config = RocketChatConfig(
    webhook_url="https://your-rocketchat.example.com/hooks/<token>",
    channel="#ops-alerts",       # optional — overrides the webhook default
    username="cronwatch",         # display name
    icon_emoji=":alarm_clock:",   # emoji avatar
    timeout=10,                   # HTTP timeout in seconds
)

notifier = RocketChatNotifier(config)
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `webhook_url` | `str` | ✅ | — | Incoming webhook URL |
| `channel` | `str` | ❌ | `""` | Override target channel (e.g. `#alerts`) |
| `username` | `str` | ❌ | `"cronwatch"` | Bot display name |
| `icon_emoji` | `str` | ❌ | `":alarm_clock:"` | Bot avatar emoji |
| `timeout` | `int` | ❌ | `10` | Request timeout (seconds) |
| `extra_fields` | `dict` | ❌ | `{}` | Merged into the webhook payload |

## Usage with CronChecker

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry, notifiers=[notifier])
checker.check_all()
```
