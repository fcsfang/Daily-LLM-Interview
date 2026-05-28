from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests


def notify(output_path: Path, *, subject_prefix: str = "Daily LLM Interview Digest") -> list[str]:
    """Send the generated digest through configured notification channels."""
    sent: list[str] = []
    text = output_path.read_text(encoding="utf-8")
    subject = f"{subject_prefix} - {output_path.stem}"

    if _smtp_enabled():
        _send_email(subject=subject, body=text)
        sent.append("email")

    webhook_url = os.getenv("DIGEST_WEBHOOK_URL")
    if webhook_url:
        _send_webhook(webhook_url=webhook_url, subject=subject, body=text)
        sent.append("webhook")

    return sent


def _smtp_enabled() -> bool:
    required = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_TO"]
    return all(os.getenv(name) for name in required)


def _send_email(subject: str, body: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.getenv("MAIL_FROM", username)
    recipients = [item.strip() for item in os.environ["MAIL_TO"].split(",") if item.strip()]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    use_ssl = _env_flag("SMTP_USE_SSL", default=port == 465)
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=30) as smtp:
        smtp.ehlo()
        if not use_ssl and _env_flag("SMTP_USE_TLS", default=True):
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _send_webhook(webhook_url: str, subject: str, body: str) -> None:
    response = requests.post(
        webhook_url,
        json={"title": subject, "content": body},
        timeout=30,
    )
    response.raise_for_status()
