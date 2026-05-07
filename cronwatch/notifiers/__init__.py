"""Notifier registry for cronwatch."""

from cronwatch.notifiers.base import AlertPayload, BaseNotifier
from cronwatch.notifiers.email_notifier import EmailConfig, EmailNotifier
from cronwatch.notifiers.log_notifier import LogNotifier
from cronwatch.notifiers.opsgenie_notifier import OpsGenieConfig, OpsGenieNotifier
from cronwatch.notifiers.pagerduty_notifier import PagerDutyConfig, PagerDutyNotifier
from cronwatch.notifiers.slack_notifier import SlackConfig, SlackNotifier
from cronwatch.notifiers.victorops_notifier import VictorOpsConfig, VictorOpsNotifier
from cronwatch.notifiers.webhook_notifier import WebhookNotifier

__all__ = [
    "AlertPayload",
    "BaseNotifier",
    "EmailConfig",
    "EmailNotifier",
    "LogNotifier",
    "OpsGenieConfig",
    "OpsGenieNotifier",
    "PagerDutyConfig",
    "PagerDutyNotifier",
    "SlackConfig",
    "SlackNotifier",
    "VictorOpsConfig",
    "VictorOpsNotifier",
    "WebhookNotifier",
]
