from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models import Appointment, AppointmentStatus, Doctor, Hospital, TriageResult, UserRole
from app.models.enums import UrgencyLevel

IST = ZoneInfo("Asia/Kolkata")


def next_slot(days_ahead=2, hour=10):
    d = datetime.now(IST).date() + timedelta(days=days_ahead)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return datetime.combine(d, time(hour), tzinfo=IST)


@pytest.fixture
def setup(db, make_user, auth_headers):
    """Two doctors (one linked to a login), one patient."""
    h = Hospital(name="H", city="Mohali", address="A")
    doc_user = make_user(email="doc@example.com", role=UserRole.doctor, name="Dr. Login")
    mine = Doctor(name="Dr. Mine", specialty="Dermatologist", bio="", hospital=h, user_id=doc_user.id)
    other = Doctor(name="Dr. Other", specialty="Dermatologist", bio="", hospital=h)
    db.add_all([mine, other])
    db.commit()
    make_user(email="pat@example.com", name="Pat Patient")
    return {
        "mine": mine,
        "other": other,
        "doc": auth_headers("doc@example.com"),
        "pat": auth_headers("pat@example.com"),
    }


def book(client, headers, doctor_id, when, triage_id=None):
    r = client.post("/api/appointments", headers=headers, json={
        "doctor_id": doctor_id, "scheduled_at": when.isoformat(), "reason": "Rash on arm",
        "triage_result_id": triage_id})
    assert r.status_code == 201, r.text
    return r.json()


def test_doctor_sees_only_own_appointments(client, setup):
    book(client, setup["pat"], setup["mine"].id, next_slot(hour=10))
    book(client, setup["pat"], setup["other"].id, next_slot(hour=11))
    items = client.get("/api/doctor/appointments", headers=setup["doc"]).json()
    assert len(items) == 1
    assert items[0]["patient"]["name"] == "Pat Patient"
    assert items[0]["triage"] is None


def test_me_returns_profile_and_stats(client, setup):
    book(client, setup["pat"], setup["mine"].id, next_slot())
    body = client.get("/api/doctor/me", headers=setup["doc"]).json()
    assert body["doctor"]["name"] == "Dr. Mine"
    assert body["stats"]["upcoming"] == 1
    assert body["stats"]["awaiting_confirmation"] == 1


def test_confirm_flow(client, setup):
    appt = book(client, setup["pat"], setup["mine"].id, next_slot())
    r = client.post(f"/api/doctor/appointments/{appt['id']}/confirm", headers=setup["doc"])
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed"
    assert r.json()["confirmed_at"] is not None
    # confirming twice is rejected
    assert client.post(f"/api/doctor/appointments/{appt['id']}/confirm", headers=setup["doc"]).status_code == 400
    # patient sees the new status
    mine = client.get("/api/appointments/me", headers=setup["pat"]).json()
    assert mine[0]["status"] == "confirmed"


def test_cannot_touch_other_doctors_appointment(client, setup):
    appt = book(client, setup["pat"], setup["other"].id, next_slot())
    r = client.post(f"/api/doctor/appointments/{appt['id']}/confirm", headers=setup["doc"])
    assert r.status_code == 404


def test_complete_only_after_start(client, setup, db):
    future = book(client, setup["pat"], setup["mine"].id, next_slot())
    assert client.post(f"/api/doctor/appointments/{future['id']}/complete", headers=setup["doc"]).status_code == 400

    past = Appointment(patient_id=2, doctor_id=setup["mine"].id, reason="Past visit",
                       scheduled_at=datetime.now(timezone.utc) - timedelta(days=1))
    db.add(past)
    db.commit()
    pending = client.get("/api/doctor/appointments?scope=pending", headers=setup["doc"]).json()
    assert [a["id"] for a in pending] == [past.id]
    r = client.post(f"/api/doctor/appointments/{past.id}/complete", headers=setup["doc"])
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    history = client.get("/api/doctor/appointments?scope=history", headers=setup["doc"]).json()
    assert [a["id"] for a in history] == [past.id]


def test_triage_summary_and_urgent_count(client, setup, db):
    tr = TriageResult(patient_id=2, image_path="2/x.jpg", predicted_condition="mel", confidence=0.8,
                      urgency_level=UrgencyLevel.high, specialist_type="Dermato-oncologist")
    db.add(tr)
    db.commit()
    book(client, setup["pat"], setup["mine"].id, next_slot(), triage_id=tr.id)
    item = client.get("/api/doctor/appointments", headers=setup["doc"]).json()[0]
    assert item["triage"]["predicted_label"] == "Melanoma"
    assert item["triage"]["urgent_referral"] is True
    assert client.get("/api/doctor/me", headers=setup["doc"]).json()["stats"]["urgent_upcoming"] == 1


def test_patients_cannot_use_doctor_portal(client, setup):
    assert client.get("/api/doctor/appointments", headers=setup["pat"]).status_code == 403


def test_unlinked_doctor_gets_clear_error(client, make_user, auth_headers):
    make_user(email="newdoc@example.com", role=UserRole.doctor)
    r = client.get("/api/doctor/me", headers=auth_headers("newdoc@example.com"))
    assert r.status_code == 403
    assert "linked" in r.json()["detail"]


def test_admin_links_doctor_account(client, setup, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    admin = auth_headers("admin@example.com")
    newdoc = make_user(email="newdoc@example.com", role=UserRole.doctor)
    r = client.patch(f"/api/admin/doctors/{setup['other'].id}/link", json={"user_id": newdoc.id}, headers=admin)
    assert r.status_code == 200
    assert client.get("/api/doctor/me", headers=auth_headers("newdoc@example.com")).json()["doctor"]["name"] == "Dr. Other"
    # a patient account can't be linked
    pat_id = client.get("/api/users/me", headers=setup["pat"]).json()["id"]
    r = client.patch(f"/api/admin/doctors/{setup['other'].id}/link", json={"user_id": pat_id}, headers=admin)
    assert r.status_code == 400
