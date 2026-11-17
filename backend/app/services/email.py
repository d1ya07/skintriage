"""Minimal email sender (standard library only).

EMAIL_BACKEND=disabled -> nothing is sent
EMAIL_BACKEND=console  -> the email is printed to the server log
EMAIL_BACKEND=smtp     -> sent through SMTP_HOST:SMTP_PORT (Mailpit locally, Gmail/Brevo in production)
"""
import logging
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.core.config import settings

log = logging.getLogger("uvicorn.error")


@dataclass
class OutgoingEmail:
    to: str
    subject: str
    text: str
    html: str
    # (filename, data, maintype, subtype)
    attachments: list[tuple[str, bytes, str, str]] = field(default_factory=list)


def build_message(e: OutgoingEmail) -> EmailMessage:
    m = EmailMessage()
    m["From"] = settings.EMAIL_FROM
    m["To"] = e.to
    m["Subject"] = e.subject
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain="skintriage.local")
    m.set_content(e.text)
    m.add_alternative(e.html, subtype="html")
    for name, data, maintype, subtype in e.attachments:
        m.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    return m


def send_email(e: OutgoingEmail) -> bool:
    backend = settings.EMAIL_BACKEND
    if backend == "disabled":
        return False
    msg = build_message(e)
    if backend == "console":
        log.info("📧 [console email] To: %s | Subject: %s\n%s", e.to, e.subject, e.text)
        return True
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_STARTTLS:
                s.starttls(context=ssl.create_default_context())
            if settings.SMTP_USERNAME:
                s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            s.send_message(msg)
        log.info("📧 Sent '%s' to %s", e.subject, e.to)
        return True
    except Exception:
        log.exception("Email to %s failed", e.to)
        return False
