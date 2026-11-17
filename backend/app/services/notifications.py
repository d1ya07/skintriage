"""Appointment notification emails. Each notify_* runs as a FastAPI background task
(after the response is sent), opens its own DB session, and never raises."""
import html
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.db.session import SessionLocal
from app.ml.rules import get_rules
from app.models import Appointment, Doctor
from app.models.enums import UrgencyLevel
from app.services import email
from app.services.scheduling import CLINIC_TZ

log = logging.getLogger("uvicorn.error")

DISCLAIMER = (
    "SkinTriage is a clinical decision-support tool, not a diagnostic device. "
    "If you think you have a medical emergency, call 112."
)


# ---------------------------------------------------------------- helpers
def _when(dt: datetime) -> str:
    return dt.astimezone(CLINIC_TZ).strftime("%a, %d %b %Y at %I:%M %p IST")


def _ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics(appt: Appointment, cancel: bool = False) -> bytes:
    fmt = "%Y%m%dT%H%M%SZ"
    start = appt.scheduled_at.astimezone(timezone.utc)
    end = start + timedelta(minutes=settings.SLOT_MINUTES)
    d, h = appt.doctor, appt.doctor.hospital
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SkinTriage//Appointments//EN",
        f"METHOD:{'CANCEL' if cancel else 'PUBLISH'}",
        "BEGIN:VEVENT",
        f"UID:appointment-{appt.id}@skintriage",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime(fmt)}",
        f"DTSTART:{start.strftime(fmt)}",
        f"DTEND:{end.strftime(fmt)}",
        f"SUMMARY:{_ics_escape(f'Appointment with {d.name} ({d.specialty})')}",
        f"LOCATION:{_ics_escape(f'{h.name}, {h.address}, {h.city}')}",
        f"DESCRIPTION:{_ics_escape(f'Reason: {appt.reason}')}",
        f"STATUS:{'CANCELLED' if cancel else 'CONFIRMED'}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return ("\r\n".join(lines) + "\r\n").encode()


def _rows(appt: Appointment, include_patient: bool = False) -> list[tuple[str, str]]:
    d, h = appt.doctor, appt.doctor.hospital
    rows = []
    if include_patient:
        rows.append(("Patient", f"{appt.patient.name} ({appt.patient.email})"))
    rows += [
        ("Doctor", f"{d.name} ({d.specialty})"),
        ("When", _when(appt.scheduled_at)),
        ("Where", f"{h.name}, {h.address}, {h.city}"),
        ("Reason", appt.reason),
    ]
    tr = appt.triage_result
    if tr is not None:
        cond = get_rules().conditions.get(tr.predicted_condition)
        label = cond.label if cond else tr.predicted_condition
        rows.append(("Skin scan", f"{label} ({tr.confidence:.0%}), {tr.urgency_level.value} urgency"))
    return rows


def _html(heading: str, intro: str, rows: list[tuple[str, str]], cta: tuple[str, str] | None,
          banner: str | None = None) -> str:
    esc = html.escape
    table = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;color:#6b7280;vertical-align:top">{esc(k)}</td>'
        f'<td style="padding:6px 0;font-weight:600">{esc(v)}</td></tr>'
        for k, v in rows
    )
    banner_html = (
        f'<div style="background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;padding:12px;'
        f'border-radius:8px;margin:16px 0"><strong>{esc(banner)}</strong></div>' if banner else ""
    )
    button = (
        f'<p style="margin:24px 0"><a href="{esc(cta[1])}" style="background:#111827;color:#fff;'
        f'padding:10px 18px;border-radius:8px;text-decoration:none">{esc(cta[0])}</a></p>' if cta else ""
    )
    return f"""<!doctype html><html><body style="margin:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111827">
<div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;padding:28px">
  <p style="font-size:18px;font-weight:700;margin:0 0 16px">🩺 SkinTriage</p>
  <h1 style="font-size:20px;margin:0 0 8px">{esc(heading)}</h1>
  <p style="margin:0 0 8px">{esc(intro)}</p>
  {banner_html}
  <table style="border-collapse:collapse;margin:16px 0;font-size:14px">{table}</table>
  {button}
  <p style="font-size:12px;color:#6b7280;border-top:1px solid #e5e7eb;padding-top:12px">{esc(DISCLAIMER)}</p>
</div></body></html>"""


def _text(greeting: str, intro: str, rows: list[tuple[str, str]], link: tuple[str, str] | None) -> str:
    body = "\n".join(f"{k}: {v}" for k, v in rows)
    link_line = f"\n\n{link[0]}: {link[1]}" if link else ""
    return f"{greeting}\n\n{intro}\n\n{body}{link_line}\n\n{DISCLAIMER}\n"


def _send(to: str, subject: str, greeting: str, heading: str, intro: str, rows, cta, ics: bytes | None,
          banner: str | None = None) -> None:
    attachments = [("appointment.ics", ics, "text", "calendar")] if ics else []
    email.send_email(email.OutgoingEmail(
        to=to,
        subject=subject,
        text=_text(greeting, intro, rows, cta),
        html=_html(heading, intro, rows, cta, banner),
        attachments=attachments,
    ))


def _load(db, appointment_id: int):
    return db.get(
        Appointment,
        appointment_id,
        options=[
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(Doctor.hospital),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.triage_result),
        ],
    )


def _run(appointment_id: int, builder: Callable[[Appointment], None]) -> None:
    db = SessionLocal()
    try:
        appt = _load(db, appointment_id)
        if appt is not None:
            builder(appt)
    except Exception:  # a failed email must never break the app
        log.exception("Notification for appointment %s failed", appointment_id)
    finally:
        db.close()


def _doctor_email(appt: Appointment) -> str | None:
    u = appt.doctor.user
    return u.email if u is not None and u.is_active else None


def _is_urgent(appt: Appointment) -> bool:
    return appt.triage_result is not None and appt.triage_result.urgency_level == UrgencyLevel.high


# ---------------------------------------------------------------- events
def notify_booked(appointment_id: int) -> None:
    def build(appt: Appointment) -> None:
        p, d = appt.patient, appt.doctor
        when = _when(appt.scheduled_at)
        _send(
            p.email,
            f"Appointment booked: {d.name}, {when}",
            f"Hi {p.name},",
            "Your appointment is booked",
            f"Your appointment with {d.name} is booked. A calendar invite is attached.",
            _rows(appt),
            ("Manage your appointments", f"{settings.FRONTEND_URL}/appointments"),
            _ics(appt),
            banner="This booking follows an urgent skin-scan result. If things get worse before your visit, seek care sooner."
            if _is_urgent(appt) else None,
        )
        doc = _doctor_email(appt)
        if doc:
            urgent = _is_urgent(appt)
            _send(
                doc,
                f"{'URGENT: ' if urgent else ''}New appointment: {p.name}, {when}",
                f"Dear {d.name},",
                "New appointment booked",
                f"{p.name} has booked an appointment with you. Please confirm it in your dashboard.",
                _rows(appt, include_patient=True),
                ("Open doctor dashboard", f"{settings.FRONTEND_URL}/doctor"),
                _ics(appt),
                banner="Linked skin scan flagged HIGH urgency (urgent referral)." if urgent else None,
            )

    _run(appointment_id, build)


def notify_confirmed(appointment_id: int) -> None:
    def build(appt: Appointment) -> None:
        p, d = appt.patient, appt.doctor
        _send(
            p.email,
            f"Appointment confirmed: {d.name}, {_when(appt.scheduled_at)}",
            f"Hi {p.name},",
            "Your appointment is confirmed",
            f"{d.name} has confirmed your appointment.",
            _rows(appt),
            ("View your appointments", f"{settings.FRONTEND_URL}/appointments"),
            _ics(appt),
        )

    _run(appointment_id, build)


def notify_cancelled(appointment_id: int) -> None:
    def build(appt: Appointment) -> None:
        p, d = appt.patient, appt.doctor
        when = _when(appt.scheduled_at)
        _send(
            p.email,
            f"Appointment cancelled: {d.name}, {when}",
            f"Hi {p.name},",
            "Your appointment is cancelled",
            "Your appointment has been cancelled and the slot released. You can book a new one at any time.",
            _rows(appt),
            ("Book a new appointment", f"{settings.FRONTEND_URL}/doctors"),
            _ics(appt, cancel=True),
        )
        doc = _doctor_email(appt)
        if doc:
            _send(
                doc,
                f"Cancelled: {p.name}, {when}",
                f"Dear {d.name},",
                "Appointment cancelled",
                f"{p.name} cancelled this appointment. The slot is free again.",
                _rows(appt, include_patient=True),
                ("Open doctor dashboard", f"{settings.FRONTEND_URL}/doctor"),
                _ics(appt, cancel=True),
            )

    _run(appointment_id, build)
