"""Notifier registry and convenience imports."""

from cronwatch.notifiers.base import AlertPayload, BaseNotifier
from cronwatch.notifiers.log_notifier import LogNotifier
from cronwatch.notifiers.webhook_notifier import WebhookNotifier
from cronwatch.notifiers.email_notifier import EmailNotifier
from cronwatch.notifiers.slack_notifier import SlackNotifier
from cronwatch.notifiers.pagerduty_notifier import PagerDutyNotifier
from cronwatch.notifiers.opsgenie_notifier import OpsGenieNotifier
from cronwatch.notifiers.victorops_notifier import VictorOpsNotifier
from cronwatch.notifiers.sns_notifier import SNSNotifier
from cronwatch.notifiers.teams_notifier import TeamsNotifier, TeamsConfig

__all__ = [
    "AlertPayload",
    "BaseNotifier",
    "LogNotifier",
    "WebhookNotifier",
    "EmailNotifier",
    "SlackNotifier",
    "PagerDutyNotifier",
    "OpsGenieNotifier",
    "VictorOpsNotifier",
    "SNSNotifier",
    "TeamsNotifier",
    "TeamsConfig",
]
