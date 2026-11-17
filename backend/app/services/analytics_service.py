"""Platform analytics computed only from data the app already stores (no extra user tracking)."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.rules import get_rules
from app.models import Appointment, AppointmentStatus, TriageResult
from app.models.enums import UrgencyLevel
from app.schemas.analytics import AnalyticsOut, ConditionCount, DailyPoint, UrgencyStat
from app.services.scheduling import CLINIC_TZ


def _rate(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


def compute(db: Session, days: int = 30) -> AnalyticsOut:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    rules = get_rules()

    scans = list(db.scalars(select(TriageResult).where(TriageResult.created_at >= since)).all())
    appts = list(db.scalars(select(Appointment).where(Appointment.created_at >= since)).all())

    # First booking made from each scan (a booking counts even if it was later cancelled)
    first_booking = dict(
        db.execute(
            select(Appointment.triage_result_id, func.min(Appointment.created_at))
            .where(Appointment.triage_result_id.isnot(None))
            .group_by(Appointment.triage_result_id)
        ).all()
    )
    booked_ids = {s.id for s in scans if s.id in first_booking}
    hours = [
        (first_booking[s.id] - s.created_at).total_seconds() / 3600 for s in scans if s.id in first_booking
    ]

    by_urgency = []
    for level in UrgencyLevel:
        group = [s for s in scans if s.urgency_level == level]
        booked = sum(1 for s in group if s.id in booked_ids)
        by_urgency.append(UrgencyStat(urgency=level.value, scans=len(group), booked=booked,
                                      booking_rate=_rate(booked, len(group))))
    urgent = next(u for u in by_urgency if u.urgency == UrgencyLevel.high.value)

    by_condition = [
        ConditionCount(code=c, label=rules.conditions[c].label if c in rules.conditions else c, count=n)
        for c, n in Counter(s.predicted_condition for s in scans).most_common()
    ]

    status_counts = {s.value: 0 for s in AppointmentStatus}
    for a in appts:
        status_counts[a.status.value] += 1

    today = now.astimezone(CLINIC_TZ).date()
    scan_days = Counter(s.created_at.astimezone(CLINIC_TZ).date() for s in scans)
    booking_days = Counter(a.created_at.astimezone(CLINIC_TZ).date() for a in appts)
    daily = [
        DailyPoint(day=d, scans=scan_days[d], bookings=booking_days[d])
        for d in (today - timedelta(days=i) for i in range(days - 1, -1, -1))
    ]

    return AnalyticsOut(
        days=days,
        total_scans=len(scans),
        scans_booked=len(booked_ids),
        triage_to_booking_rate=_rate(len(booked_ids), len(scans)),
        median_hours_to_booking=round(median(hours), 1) if hours else None,
        urgent_scans=urgent.scans,
        urgent_booked=urgent.booked,
        urgent_booking_rate=urgent.booking_rate,
        uncertain_rate=_rate(sum(1 for s in scans if s.confidence < rules.uncertain_below), len(scans)),
        by_urgency=by_urgency,
        by_condition=by_condition,
        appointments_total=len(appts),
        appointments_from_scan=sum(1 for a in appts if a.triage_result_id is not None),
        appointments_by_status=status_counts,
        cancellation_rate=_rate(status_counts["cancelled"], len(appts)),
        completion_rate=_rate(status_counts["completed"], len(appts)),
        daily=daily,
    )
