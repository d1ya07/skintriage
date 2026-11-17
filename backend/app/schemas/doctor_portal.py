from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppointmentStatus, UrgencyLevel
from app.schemas.doctor import DoctorOut


class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    skin_type: Optional[str]


class TriageBrief(BaseModel):
    id: int
    predicted_condition: str
    predicted_label: str
    confidence: float
    urgency_level: UrgencyLevel
    urgent_referral: bool


class DoctorAppointmentOut(BaseModel):
    id: int
    scheduled_at: datetime
    reason: str
    status: AppointmentStatus
    created_at: datetime
    cancelled_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]
    patient: PatientBrief
    triage: Optional[TriageBrief]


class DoctorStats(BaseModel):
    today: int
    upcoming: int
    awaiting_confirmation: int
    to_complete: int
    completed: int
    urgent_upcoming: int


class DoctorMeOut(BaseModel):
    doctor: DoctorOut
    stats: DoctorStats


class DoctorLinkIn(BaseModel):
    user_id: Optional[int]  # null to unlink
