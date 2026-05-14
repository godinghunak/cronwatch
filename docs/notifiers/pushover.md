# Pushover Notifier

Send cronwatch alerts as push notifications via [Pushover](https://pushover.net/).

## Prerequisites

1. Create a Pushover account and register an **Application/API Token**.
2. Collect the **User Key** (or Group Key) for each recipient.

## Configuration

```python
from cronwatch.notifiers.pushover_notifier import PushoverConfig, PushoverNotifier

config = PushoverConfig(
    api_token="your_application_api_token",
    user_keys=["user_or_group_key_1", "user_or_group_key_2"],
    priority=0,       # -2 (lowest) to 2 (emergency), default 0
    sound="falling",  # Pushover sound name, default "falling"
    timeout=10,       # HTTP request timeout in seconds
)

notifier = PushoverNotifier(config)
```

## Priority Levels

| Value | Meaning              |
|-------|----------------------|
| -2    | No notification/sound|
| -1    | Quiet                |
|  0    | Normal (default)     |
|  1    | High priority        |
|  2    | Emergency (requires acknowledgement) |

## Usage with CronChecker

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry=registry, notifiers=[notifier])
checker.check_all()
```

## Notes

- One API request is made per `user_key`.
- If `user_keys` is empty, no requests are sent.
- `raise_for_status()` is called on every response; HTTP errors propagate as exceptions.
