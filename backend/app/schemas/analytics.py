from datetime import date
from typing import Optional

from pydantic import BaseModel


class UrgencyStat(BaseModel):
    urgency: str
    scans: int
    booked: int
    booking_rate: float


class ConditionCount(BaseModel):
    code: str
    label: str
    count: int


class DailyPoint(BaseModel):
    day: date
    scans: int
    bookings: int


class AnalyticsOut(BaseModel):
    days: int
    # triage funnel
    total_scans: int
    scans_booked: int
    triage_to_booking_rate: float
    median_hours_to_booking: Optional[float]
    urgent_scans: int
    urgent_booked: int
    urgent_booking_rate: float
    uncertain_rate: float
    by_urgency: list[UrgencyStat]
    by_condition: list[ConditionCount]
    # appointments
    appointments_total: int
    appointments_from_scan: int
    appointments_by_status: dict[str, int]
    cancellation_rate: float
    completion_rate: float
    # trend
    daily: list[DailyPoint]
