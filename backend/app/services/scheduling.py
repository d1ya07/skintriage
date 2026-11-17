from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Appointment, AppointmentStatus

CLINIC_TZ = ZoneInfo(settings.CLINIC_TIMEZONE)


def day_slots(day: date) -> list[datetime]:
    """All bookable slot start times for a day (clinic is closed on Sundays)."""
    if day.weekday() == 6:
        return []
    start = datetime.combine(day, time(settings.CLINIC_OPEN_HOUR), tzinfo=CLINIC_TZ)
    end = datetime.combine(day, time(settings.CLINIC_CLOSE_HOUR), tzinfo=CLINIC_TZ)
    step = timedelta(minutes=settings.SLOT_MINUTES)
    slots, t = [], start
    while t < end:
        slots.append(t)
        t += step
    return slots


def is_valid_slot(when: datetime) -> bool:
    local = when.astimezone(CLINIC_TZ)
    return local in day_slots(local.date())


def available_slots(db: Session, doctor_id: int, day: date) -> list[datetime]:
    slots = day_slots(day)
    if not slots:
        return []
    taken = set(
        db.scalars(
            select(Appointment.scheduled_at).where(
                Appointment.doctor_id == doctor_id,
                Appointment.status != AppointmentStatus.cancelled,
                Appointment.scheduled_at >= slots[0],
                Appointment.scheduled_at <= slots[-1],
            )
        ).all()
    )
    now = datetime.now(timezone.utc)
    return [s for s in slots if s > now and s not in taken]
