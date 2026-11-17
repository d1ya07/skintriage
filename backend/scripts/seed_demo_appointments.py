"""Give the demo doctor (Dr. Anika Mehta) some appointments to work with:
a past one to complete, upcoming ones to confirm, and one linked to the demo patient's skin scan.
Safe to run more than once. Run from backend/:  python scripts/seed_demo_appointments.py
"""
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import Appointment, AppointmentStatus, Doctor, TriageResult, User  # noqa: E402
from app.models.enums import UrgencyLevel  # noqa: E402
from app.services.scheduling import CLINIC_TZ  # noqa: E402


def open_day(offset: int):
    d = datetime.now(CLINIC_TZ).date() + timedelta(days=offset)
    step = 1 if offset >= 0 else -1
    while d.weekday() == 6:  # clinic closed on Sunday
        d += timedelta(days=step)
    return d


def main():
    db = SessionLocal()
    try:
        patient = db.scalar(select(User).where(User.email == "patient@skintriage.app"))
        doctor = db.scalar(select(Doctor).where(Doctor.name == "Dr. Anika Mehta"))
        if not patient or not doctor:
            raise SystemExit("❌ Run scripts/seed.py first")
        if doctor.user_id is None:
            raise SystemExit("❌ Dr. Anika Mehta isn't linked to doctor@skintriage.app. Run scripts/seed.py again")

        scan = db.scalar(
            select(TriageResult)
            .where(TriageResult.patient_id == patient.id)
            .order_by((TriageResult.urgency_level == UrgencyLevel.high).desc(), TriageResult.created_at.desc())
        )

        now = datetime.now(timezone.utc)
        plan = [
            (open_day(-2), time(15, 30), AppointmentStatus.completed, "Routine mole check", None),
            (open_day(-1), time(11, 0), AppointmentStatus.booked, "Itchy patch on forearm for two weeks", None),
            (open_day(1), time(10, 0), AppointmentStatus.booked, "Mole on back has changed shape",
             scan.id if scan else None),
            (open_day(2), time(14, 30), AppointmentStatus.confirmed, "Follow-up on eczema flare", None),
            (open_day(3), time(12, 0), AppointmentStatus.booked, "Dry scaly patch on scalp", None),
        ]

        created = 0
        for day, t, status, reason, triage_id in plan:
            when = datetime.combine(day, t, tzinfo=CLINIC_TZ)
            clash = db.scalar(
                select(Appointment.id).where(
                    Appointment.status != AppointmentStatus.cancelled,
                    (Appointment.doctor_id == doctor.id) | (Appointment.patient_id == patient.id),
                    Appointment.scheduled_at == when,
                )
            )
            if clash:
                continue
            db.add(Appointment(
                patient_id=patient.id, doctor_id=doctor.id, scheduled_at=when, reason=reason,
                status=status, triage_result_id=triage_id,
                confirmed_at=now if status == AppointmentStatus.confirmed else None,
                completed_at=now if status == AppointmentStatus.completed else None,
            ))
            created += 1
        db.commit()
        print(f"✅ Added {created} demo appointment(s) for {doctor.name}"
              + (f" (one linked to skin scan #{scan.id})" if scan else " (no skin scan found to link)"))
    finally:
        db.close()


if __name__ == "__main__":
    main()
