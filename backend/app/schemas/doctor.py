from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    address: str


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: str
    bio: Optional[str]
    hospital: HospitalOut


class SlotsOut(BaseModel):
    doctor_id: int
    day: date
    timezone: str
    slots: list[datetime]
