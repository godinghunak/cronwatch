"""Email notifier that sends alert payloads via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import List

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int = 587
    use_tls: bool = True
    username: str = ""
    password: str = ""
    sender: str = ""
    recipients: List[str] = field(default_factory=list)


class EmailNotifier(BaseNotifier):
    """Sends alert e-mails through an SMTP server."""

    def __init__(self, config: EmailConfig) -> None:
        self.config = config

    def send(self, payload: AlertPayload) -> None:
        cfg = self.config
        if not cfg.recipients:
            logger.warning("EmailNotifier: no recipients configured, skipping.")
            return

        subject = f"[cronwatch] Alert for job '{payload.job_name}'"
        body = payload.summary()

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg.sender or cfg.username
        msg["To"] = ", ".join(cfg.recipients)
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                if cfg.use_tls:
                    server.starttls()
                if cfg.username and cfg.password:
                    server.login(cfg.username, cfg.password)
                server.sendmail(
                    msg["From"],
                    cfg.recipients,
                    msg.as_string(),
                )
            logger.info(
                "EmailNotifier: alert sent for job '%s' to %s",
                payload.job_name,
                cfg.recipients,
            )
        except smtplib.SMTPException as exc:
            logger.error(
                "EmailNotifier: failed to send alert for job '%s': %s",
                payload.job_name,
                exc,
            )
            raise
