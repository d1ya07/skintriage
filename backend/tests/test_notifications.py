from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.config import settings
from app.models import Doctor, Hospital, TriageResult, UserRole
from app.models.enums import UrgencyLevel
from app.services import email

IST = ZoneInfo("Asia/Kolkata")


def next_slot(days_ahead=2, hour=10):
    d = datetime.now(IST).date() + timedelta(days=days_ahead)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return datetime.combine(d, time(hour), tzinfo=IST)


@pytest.fixture
def outbox(monkeypatch):
    sent: list[email.OutgoingEmail] = []
    monkeypatch.setattr(email, "send_email", lambda e: sent.append(e) or True)
    return sent


@pytest.fixture
def world(db, make_user, auth_headers):
    h = Hospital(name="Sunrise Clinic", city="Mohali", address="Sector 70")
    doc_user = make_user(email="doc@example.com", role=UserRole.doctor, name="Dr. Login")
    doctor = Doctor(name="Dr. Mehta", specialty="Dermatologist", bio="", hospital=h, user_id=doc_user.id)
    db.add(doctor)
    db.commit()
    make_user(email="pat@example.com", name="Pat Patient")
    return {"doctor": doctor, "pat": auth_headers("pat@example.com"), "doc": auth_headers("doc@example.com")}


def book(client, headers, doctor_id, triage_id=None):
    r = client.post("/api/appointments", headers=headers, json={
        "doctor_id": doctor_id, "scheduled_at": next_slot().isoformat(), "reason": "Mole changed shape",
        "triage_result_id": triage_id})
    assert r.status_code == 201, r.text
    return r.json()


def ics_of(e: email.OutgoingEmail) -> str:
    return e.attachments[0][1].decode()


def test_booking_emails_patient_and_doctor(client, world, outbox):
    book(client, world["pat"], world["doctor"].id)
    assert [e.to for e in outbox] == ["pat@example.com", "doc@example.com"]
    patient_mail = outbox[0]
    assert patient_mail.subject.startswith("Appointment booked: Dr. Mehta")
    assert "IST" in patient_mail.subject
    assert "Sunrise Clinic" in patient_mail.text and "Sunrise Clinic" in patient_mail.html
    assert "not a diagnostic device" in patient_mail.text
    cal = ics_of(patient_mail)
    assert "METHOD:PUBLISH" in cal and "DTSTART:" in cal and "Dr. Mehta" in cal


def test_cancel_sends_calendar_cancellation(client, world, outbox):
    appt = book(client, world["pat"], world["doctor"].id)
    outbox.clear()
    client.post(f"/api/appointments/{appt['id']}/cancel", headers=world["pat"])
    assert outbox[0].subject.startswith("Appointment cancelled")
    assert "METHOD:CANCEL" in ics_of(outbox[0])
    assert outbox[1].to == "doc@example.com"


def test_doctor_confirm_emails_patient(client, world, outbox):
    appt = book(client, world["pat"], world["doctor"].id)
    outbox.clear()
    client.post(f"/api/doctor/appointments/{appt['id']}/confirm", headers=world["doc"])
    assert len(outbox) == 1
    assert outbox[0].to == "pat@example.com"
    assert outbox[0].subject.startswith("Appointment confirmed")


def test_urgent_scan_is_highlighted_for_doctor(client, world, outbox, db):
    tr = TriageResult(patient_id=2, image_path="2/x.jpg", predicted_condition="mel", confidence=0.8,
                      urgency_level=UrgencyLevel.high, specialist_type="Dermato-oncologist")
    db.add(tr)
    db.commit()
    book(client, world["pat"], world["doctor"].id, triage_id=tr.id)
    doctor_mail = outbox[1]
    assert doctor_mail.subject.startswith("URGENT:")
    assert "Melanoma" in doctor_mail.text


def test_email_failure_never_breaks_booking(client, world, monkeypatch):
    def boom(e):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(email, "send_email", boom)
    book(client, world["pat"], world["doctor"].id)  # still 201


def test_html_escapes_user_text(client, world, outbox):
    r = client.post("/api/appointments", headers=world["pat"], json={
        "doctor_id": world["doctor"].id, "scheduled_at": next_slot().isoformat(),
        "reason": "<script>alert(1)</script>"})
    assert r.status_code == 201
    assert "<script>" not in outbox[0].html
    assert "&lt;script&gt;" in outbox[0].html


def test_smtp_backend_builds_proper_message(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured["addr"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def send_message(self, msg):
            captured["msg"] = msg

    monkeypatch.setattr(settings, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
    ok = email.send_email(email.OutgoingEmail(
        to="a@example.com", subject="Hi", text="plain", html="<b>html</b>",
        attachments=[("appointment.ics", b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", "text", "calendar")]))
    assert ok
    parts = [p.get_content_type() for p in captured["msg"].walk()]
    assert parts == ["multipart/mixed", "multipart/alternative", "text/plain", "text/html", "text/calendar"]


def test_disabled_backend_sends_nothing(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_BACKEND", "disabled")
    assert email.send_email(email.OutgoingEmail(to="a@b.co", subject="x", text="x", html="x")) is False
