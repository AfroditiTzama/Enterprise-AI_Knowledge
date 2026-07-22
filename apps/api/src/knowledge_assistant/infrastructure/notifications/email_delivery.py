import asyncio
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage as SMTPMessage
from pathlib import Path
from uuid import uuid4

from knowledge_assistant.domain.notifications.email_delivery import (
    EmailDelivery,
    EmailMessage,
)


class LocalOutboxEmailDelivery(EmailDelivery):
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._write_message, message)

    def _write_message(self, message: EmailMessage) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = self._directory / f"{timestamp}_{uuid4().hex}.eml"
        path.write_text(
            "\n".join(
                [
                    f"To: {message.recipient}",
                    f"Subject: {message.subject}",
                    "Content-Type: text/plain; charset=utf-8",
                    "",
                    message.text_body,
                    "",
                ]
            ),
            encoding="utf-8",
        )


class SMTPEmailDelivery(EmailDelivery):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_address: str,
        use_tls: bool,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._use_tls = use_tls

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        email = SMTPMessage()
        email["From"] = self._from_address
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email.set_content(message.text_body)

        with smtplib.SMTP(self._host, self._port, timeout=20) as client:
            if self._use_tls:
                client.starttls()
            if self._username:
                client.login(self._username, self._password or "")
            client.send_message(email)
