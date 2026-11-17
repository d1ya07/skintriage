from datetime import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.models.enums import AppointmentStatus
from app.schemas.doctor import DoctorOut


class AppointmentCreate(BaseModel):
    doctor_id: int
    scheduled_at: AwareDatetime  # must include a timezone, e.g. 2026-11-20T10:00:00+05:30
    reason: str = Field(min_length=3, max_length=500)
    triage_result_id: Optional[int] = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor: DoctorOut
    scheduled_at: datetime
    reason: str
    status: AppointmentStatus
    created_at: datetime
    cancelled_at: Optional[datetime]
    triage_result_id: Optional[int]
