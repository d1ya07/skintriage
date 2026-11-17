from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import Appointment, AppointmentStatus, Doctor, TriageResult, User
from app.schemas.appointment import AppointmentCreate
from app.services.scheduling import is_valid_slot

Scope = Literal["upcoming", "past", "all"]


def _active_clash(db: Session, *conditions) -> bool:
    stmt = select(Appointment.id).where(
        Appointment.status != AppointmentStatus.cancelled, *conditions
    )
    return db.scalar(stmt) is not None


def create(db: Session, patient: User, data: AppointmentCreate) -> Appointment:
    doctor = db.get(Doctor, data.doctor_id)
    if not doctor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")

    when = data.scheduled_at
    now = datetime.now(timezone.utc)
    if when <= now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Appointment time must be in the future")
    if when > now + timedelta(days=settings.BOOKING_WINDOW_DAYS):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"You can book at most {settings.BOOKING_WINDOW_DAYS} days ahead",
        )
    if not is_valid_slot(when):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Pick one of the available slots (Mon to Sat, 30-minute slots in clinic hours)",
        )

    if data.triage_result_id is not None:
        tr = db.get(TriageResult, data.triage_result_id)
        if not tr or tr.patient_id != patient.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid triage result")

    if _active_clash(db, Appointment.doctor_id == doctor.id, Appointment.scheduled_at == when):
        raise HTTPException(status.HTTP_409_CONFLICT, "That slot is already booked")
    if _active_clash(db, Appointment.patient_id == patient.id, Appointment.scheduled_at == when):
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an appointment at this time")

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=when,
        reason=data.reason.strip(),
        triage_result_id=data.triage_result_id,
    )
    db.add(appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # someone grabbed the slot a split second earlier
        raise HTTPException(status.HTTP_409_CONFLICT, "That slot was just taken")
    db.refresh(appt)
    return appt


def list_for_patient(db: Session, patient_id: int, scope: Scope = "all") -> list[Appointment]:
    now = datetime.now(timezone.utc)
    stmt = (
        select(Appointment)
        .where(Appointment.patient_id == patient_id)
        .options(joinedload(Appointment.doctor).joinedload(Doctor.hospital))
    )
    if scope == "upcoming":
        stmt = stmt.where(
            Appointment.scheduled_at >= now,
            Appointment.status != AppointmentStatus.cancelled,
        ).order_by(Appointment.scheduled_at.asc())
    elif scope == "past":
        stmt = stmt.where(
            or_(
                Appointment.scheduled_at < now,
                Appointment.status == AppointmentStatus.cancelled,
            )
        ).order_by(Appointment.scheduled_at.desc())
    else:
        stmt = stmt.order_by(Appointment.scheduled_at.desc())
    return list(db.scalars(stmt).unique().all())


def cancel(db: Session, patient: User, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if not appt or appt.patient_id != patient.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    if appt.status == AppointmentStatus.cancelled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Appointment is already cancelled")
    if appt.status == AppointmentStatus.completed or appt.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Past appointments can't be cancelled")
    appt.status = AppointmentStatus.cancelled
    appt.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(appt)
    return appt
