# cronwatch

Lightweight cron job monitor that sends alerts on failures or missed schedules.

## Installation

```bash
pip install cronwatch
```

## Usage

Wrap your cron command with `cronwatch` to monitor execution and receive alerts on failure or missed runs.

```bash
# Basic usage
cronwatch --job "backup" -- /usr/local/bin/backup.sh

# With a schedule to detect missed runs (cron expression)
cronwatch --job "nightly-backup" --schedule "0 2 * * *" -- /usr/local/bin/backup.sh
```

Configure alerts in `~/.cronwatch.yml`:

```yaml
alerts:
  email: ops@example.com
  slack_webhook: https://hooks.slack.com/services/your/webhook/url

jobs:
  nightly-backup:
    schedule: "0 2 * * *"
    timeout: 3600
    notify_on: [failure, missed]
```

Then add cronwatch to your crontab:

```
0 2 * * * cronwatch --job "nightly-backup" -- /usr/local/bin/backup.sh
```

cronwatch will send an alert if the job exits with a non-zero status, exceeds its timeout, or fails to run within the expected schedule window.

## Configuration Options

| Option | Description |
|---|---|
| `--job` | Unique job name for tracking |
| `--schedule` | Cron expression for missed-run detection |
| `--timeout` | Max runtime in seconds before alerting |
| `--config` | Path to config file (default: `~/.cronwatch.yml`) |

## License

MIT