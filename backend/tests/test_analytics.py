from datetime import datetime, timedelta, timezone

from app.models import Appointment, Doctor, Hospital, TriageResult, UserRole
from app.models.enums import UrgencyLevel


def scan(db, patient_id, cond, conf, urgency):
    tr = TriageResult(patient_id=patient_id, image_path=f"{patient_id}/x.jpg", predicted_condition=cond,
                      confidence=conf, urgency_level=urgency, specialist_type="Dermatologist")
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def test_analytics_funnel(client, db, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    pat = make_user(email="pat@example.com")
    doctor = Doctor(name="Dr. A", specialty="Dermatologist", bio="",
                    hospital=Hospital(name="H", city="Mohali", address="A"))
    db.add(doctor)
    db.commit()

    high = scan(db, pat.id, "mel", 0.80, UrgencyLevel.high)
    scan(db, pat.id, "nv", 0.90, UrgencyLevel.low)
    scan(db, pat.id, "bkl", 0.40, UrgencyLevel.moderate)  # uncertain (< 0.60)
    soon = datetime.now(timezone.utc) + timedelta(days=2)
    db.add(Appointment(patient_id=pat.id, doctor_id=doctor.id, triage_result_id=high.id,
                       reason="From scan", scheduled_at=soon))
    db.add(Appointment(patient_id=pat.id, doctor_id=doctor.id, reason="Routine",
                       scheduled_at=soon + timedelta(hours=1)))
    db.commit()

    r = client.get("/api/admin/analytics?days=30", headers=auth_headers("admin@example.com"))
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["total_scans"] == 3
    assert b["scans_booked"] == 1
    assert abs(b["triage_to_booking_rate"] - 1 / 3) < 0.001
    assert (b["urgent_scans"], b["urgent_booked"], b["urgent_booking_rate"]) == (1, 1, 1.0)
    assert abs(b["uncertain_rate"] - 1 / 3) < 0.001
    assert b["appointments_total"] == 2 and b["appointments_from_scan"] == 1
    assert b["median_hours_to_booking"] is not None
    assert len(b["daily"]) == 30
    assert b["daily"][-1]["scans"] == 3 and b["daily"][-1]["bookings"] == 2
    assert {c["code"] for c in b["by_condition"]} == {"mel", "nv", "bkl"}


def test_analytics_empty_is_safe(client, make_user, auth_headers):
    make_user(email="admin@example.com", role=UserRole.admin)
    b = client.get("/api/admin/analytics?days=7", headers=auth_headers("admin@example.com")).json()
    assert b["total_scans"] == 0 and b["triage_to_booking_rate"] == 0.0
    assert b["median_hours_to_booking"] is None
    assert len(b["daily"]) == 7


def test_patient_cannot_see_analytics(client, make_user, auth_headers):
    make_user(email="pat@example.com")
    assert client.get("/api/admin/analytics", headers=auth_headers("pat@example.com")).status_code == 403
