from datetime import datetime, time, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.ml.rules import get_rules
from app.models import Appointment, AppointmentStatus, Doctor, TriageResult, User
from app.models.enums import UrgencyLevel
from app.schemas.doctor_portal import (
    DoctorAppointmentOut,
    DoctorStats,
    PatientBrief,
    TriageBrief,
)
from app.services.scheduling import CLINIC_TZ

Scope = Literal["upcoming", "pending", "history", "all"]
ACTIVE = (AppointmentStatus.booked, AppointmentStatus.confirmed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_doctor_for_user(db: Session, user: User) -> Doctor:
    doctor = db.scalar(
        select(Doctor).where(Doctor.user_id == user.id).options(joinedload(Doctor.hospital))
    )
    if not doctor:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Your account isn't linked to a doctor profile yet. Please ask an administrator.",
        )
    return doctor


def _count(db: Session, *where) -> int:
    return db.scalar(select(func.count()).select_from(Appointment).where(*where)) or 0


def stats(db: Session, doctor_id: int) -> DoctorStats:
    now = _now()
    today = now.astimezone(CLINIC_TZ).date()
    day_start = datetime.combine(today, time.min, tzinfo=CLINIC_TZ)
    day_end = day_start + timedelta(days=1)
    mine = Appointment.doctor_id == doctor_id

    urgent = (
        db.scalar(
            select(func.count())
            .select_from(Appointment)
            .join(TriageResult, Appointment.triage_result_id == TriageResult.id)
            .where(
                mine,
                Appointment.scheduled_at >= now,
                Appointment.status.in_(ACTIVE),
                TriageResult.urgency_level == UrgencyLevel.high,
            )
        )
        or 0
    )
    return DoctorStats(
        today=_count(db, mine, Appointment.scheduled_at >= day_start, Appointment.scheduled_at < day_end,
                     Appointment.status != AppointmentStatus.cancelled),
        upcoming=_count(db, mine, Appointment.scheduled_at >= now, Appointment.status.in_(ACTIVE)),
        awaiting_confirmation=_count(db, mine, Appointment.scheduled_at >= now,
                                     Appointment.status == AppointmentStatus.booked),
        to_complete=_count(db, mine, Appointment.scheduled_at < now, Appointment.status.in_(ACTIVE)),
        completed=_count(db, mine, Appointment.status == AppointmentStatus.completed),
        urgent_upcoming=urgent,
    )


def list_for_doctor(db: Session, doctor_id: int, scope: Scope = "upcoming") -> list[Appointment]:
    now = _now()
    stmt = (
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .options(joinedload(Appointment.patient), joinedload(Appointment.triage_result))
    )
    if scope == "upcoming":
        stmt = stmt.where(Appointment.scheduled_at >= now, Appointment.status.in_(ACTIVE)).order_by(
            Appointment.scheduled_at.asc()
        )
    elif scope == "pending":  # time has passed but not completed yet
        stmt = stmt.where(Appointment.scheduled_at < now, Appointment.status.in_(ACTIVE)).order_by(
            Appointment.scheduled_at.asc()
        )
    elif scope == "history":
        stmt = stmt.where(
            or_(
                Appointment.status == AppointmentStatus.completed,
                Appointment.status == AppointmentStatus.cancelled,
            )
        ).order_by(Appointment.scheduled_at.desc())
    else:
        stmt = stmt.order_by(Appointment.scheduled_at.desc())
    return list(db.scalars(stmt).unique().all())


def _get_own(db: Session, doctor: Doctor, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if not appt or appt.doctor_id != doctor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    return appt


def confirm(db: Session, doctor: Doctor, appointment_id: int) -> Appointment:
    appt = _get_own(db, doctor, appointment_id)
    if appt.status != AppointmentStatus.booked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Only booked appointments can be confirmed (this one is {appt.status.value})")
    if appt.scheduled_at <= _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This appointment time has already passed")
    appt.status = AppointmentStatus.confirmed
    appt.confirmed_at = _now()
    db.commit()
    db.refresh(appt)
    return appt


def complete(db: Session, doctor: Doctor, appointment_id: int) -> Appointment:
    appt = _get_own(db, doctor, appointment_id)
    if appt.status not in ACTIVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"This appointment is already {appt.status.value}")
    if appt.scheduled_at > _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can only complete an appointment once its time has started")
    appt.status = AppointmentStatus.completed
    appt.completed_at = _now()
    db.commit()
    db.refresh(appt)
    return appt


def to_out(appt: Appointment) -> DoctorAppointmentOut:
    triage = None
    tr = appt.triage_result
    if tr is not None:
        cond = get_rules().conditions.get(tr.predicted_condition)
        triage = TriageBrief(
            id=tr.id,
            predicted_condition=tr.predicted_condition,
            predicted_label=cond.label if cond else tr.predicted_condition,
            confidence=tr.confidence,
            urgency_level=tr.urgency_level,
            urgent_referral=tr.urgency_level == UrgencyLevel.high,
            uncertain=tr.confidence < get_rules().uncertain_below,
        )
    return DoctorAppointmentOut(
        id=appt.id,
        scheduled_at=appt.scheduled_at,
        reason=appt.reason,
        status=appt.status,
        created_at=appt.created_at,
        cancelled_at=appt.cancelled_at,
        confirmed_at=appt.confirmed_at,
        completed_at=appt.completed_at,
        patient=PatientBrief.model_validate(appt.patient),
        triage=triage,
    )
