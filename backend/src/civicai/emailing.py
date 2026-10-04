from __future__ import annotations

import json
import smtplib
import ssl
import httpx
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from civicai.config import EmailSettings


@dataclass(frozen=True)
class OutboundEmail:
    recipient: str
    subject: str
    text: str


class EmailService(Protocol):
    def send(self, message: OutboundEmail) -> None: ...


class CapturingEmailService:
    """Development adapter: captures mail outside logs; never allowed in production."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.messages: list[OutboundEmail] = []

    def send(self, message: OutboundEmail) -> None:
        self.messages.append(message)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{uuid4().hex}.json"
        path.write_text(json.dumps({
            "recipient": message.recipient, "subject": message.subject, "text": message.text,
        }, ensure_ascii=False), encoding="utf-8")


class DisabledEmailService:
    def send(self, message: OutboundEmail) -> None:
        return None


class SMTPEmailService:
    def __init__(self, settings: EmailSettings):
        if not settings.smtp_host:
            raise RuntimeError("SMTP_HOST is required when EMAIL_TRANSPORT=smtp")
        self.settings = settings

    def send(self, message: OutboundEmail) -> None:
        email = EmailMessage()
        email["From"] = self.settings.from_address
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email.set_content(message.text)
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as client:
            if self.settings.smtp_starttls:
                client.starttls(context=ssl.create_default_context())
            if self.settings.smtp_username:
                client.login(self.settings.smtp_username, self.settings.smtp_password)
            client.send_message(email)


class BrevoEmailService:
    """Transactional delivery over HTTPS; errors deliberately exclude response bodies."""

    def __init__(self, settings: EmailSettings):
        if not settings.brevo_api_key or not settings.from_address:
            raise RuntimeError("BREVO_API_KEY and EMAIL_FROM are required when EMAIL_TRANSPORT=brevo")
        self.settings = settings

    def send(self, message: OutboundEmail) -> None:
        try:
            response = httpx.post(
                self.settings.brevo_api_url,
                headers={"api-key": self.settings.brevo_api_key, "accept": "application/json"},
                json={
                    "sender": {"email": self.settings.from_address},
                    "to": [{"email": message.recipient}],
                    "subject": message.subject,
                    "textContent": message.text,
                },
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("Transactional email delivery failed") from exc


def build_email_service(settings: EmailSettings) -> EmailService:
    if settings.transport == "capture":
        return CapturingEmailService(settings.capture_directory)
    if settings.transport == "smtp":
        return SMTPEmailService(settings)
    if settings.transport == "brevo":
        return BrevoEmailService(settings)
    return DisabledEmailService()
