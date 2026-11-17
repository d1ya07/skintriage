from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models import Doctor, Hospital, UserRole

IST = ZoneInfo("Asia/Kolkata")


def next_slot(days_ahead: int = 2, hour: int = 10, minute: int = 0) -> datetime:
    d = datetime.now(IST).date() + timedelta(days=days_ahead)
    while d.weekday() == 6:  # skip Sunday
        d += timedelta(days=1)
    return datetime.combine(d, time(hour, minute), tzinfo=IST)


@pytest.fixture
def doctor(db):
    h = Hospital(name="Test Hospital", city="Mohali", address="Sector 1")
    d = Doctor(name="Dr. Test", specialty="Dermatologist", bio="", hospital=h)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@pytest.fixture
def patient_headers(make_user, auth_headers):
    make_user(email="pat@example.com")
    return auth_headers("pat@example.com")


def book(client, headers, doctor_id, when, reason="Itchy rash on arm"):
    return client.post(
        "/api/appointments",
        json={"doctor_id": doctor_id, "scheduled_at": when.isoformat(), "reason": reason},
        headers=headers,
    )


def test_directory(client, doctor, patient_headers):
    r = client.get("/api/doctors", headers=patient_headers)
    assert r.status_code == 200
    assert r.json()[0]["hospital"]["name"] == "Test Hospital"
    r = client.get("/api/doctors?specialty=dermato-oncologist", headers=patient_headers)
    assert r.json() == []
    assert client.get("/api/doctors/specialties", headers=patient_headers).json() == ["Dermatologist"]


def test_book_and_list(client, doctor, patient_headers):
    r = book(client, patient_headers, doctor.id, next_slot())
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "booked"
    upcoming = client.get("/api/appointments/me?scope=upcoming", headers=patient_headers).json()
    assert len(upcoming) == 1
    assert upcoming[0]["doctor"]["name"] == "Dr. Test"


def test_double_booking_blocked(client, doctor, patient_headers, make_user, auth_headers):
    when = next_slot()
    assert book(client, patient_headers, doctor.id, when).status_code == 201
    make_user(email="other@example.com")
    r = book(client, auth_headers("other@example.com"), doctor.id, when)
    assert r.status_code == 409


def test_past_time_rejected(client, doctor, patient_headers):
    r = book(client, patient_headers, doctor.id, datetime.now(IST) - timedelta(days=1))
    assert r.status_code == 400


def test_off_grid_time_rejected(client, doctor, patient_headers):
    r = book(client, patient_headers, doctor.id, next_slot(minute=10))
    assert r.status_code == 400


def test_outside_hours_rejected(client, doctor, patient_headers):
    r = book(client, patient_headers, doctor.id, next_slot(hour=20))
    assert r.status_code == 400


def test_slots_exclude_booked(client, doctor, patient_headers):
    when = next_slot()
    day = when.date().isoformat()
    before = client.get(f"/api/doctors/{doctor.id}/slots?day={day}", headers=patient_headers).json()
    assert len(before["slots"]) == 16  # 09:00 to 16:30
    book(client, patient_headers, doctor.id, when)
    after = client.get(f"/api/doctors/{doctor.id}/slots?day={day}", headers=patient_headers).json()
    assert len(after["slots"]) == 15


def test_cancel_frees_slot(client, doctor, patient_headers):
    when = next_slot()
    appt = book(client, patient_headers, doctor.id, when).json()
    r = client.post(f"/api/appointments/{appt['id']}/cancel", headers=patient_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert r.json()["cancelled_at"] is not None
    past = client.get("/api/appointments/me?scope=past", headers=patient_headers).json()
    assert [a["id"] for a in past] == [appt["id"]]
    assert book(client, patient_headers, doctor.id, when).status_code == 201  # slot reusable


def test_cannot_cancel_someone_elses(client, doctor, patient_headers, make_user, auth_headers):
    appt = book(client, patient_headers, doctor.id, next_slot()).json()
    make_user(email="other@example.com")
    r = client.post(f"/api/appointments/{appt['id']}/cancel", headers=auth_headers("other@example.com"))
    assert r.status_code == 404


def test_doctor_cannot_book(client, doctor, make_user, auth_headers):
    make_user(email="doc@example.com", role=UserRole.doctor)
    r = book(client, auth_headers("doc@example.com"), doctor.id, next_slot())
    assert r.status_code == 403
