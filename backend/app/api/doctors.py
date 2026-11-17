from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Doctor, User
from app.schemas.doctor import DoctorOut, SlotsOut
from app.services import doctor_service
from app.services.scheduling import available_slots

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
def list_doctors(
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return doctor_service.list_doctors(db, specialty=specialty, city=city, q=q)


@router.get("/specialties", response_model=list[str])
def specialties(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return doctor_service.list_specialties(db)


@router.get("/cities", response_model=list[str])
def cities(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return doctor_service.list_cities(db)


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    return doctor


@router.get("/{doctor_id}/slots", response_model=SlotsOut)
def get_slots(
    doctor_id: int,
    day: date = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not db.get(Doctor, doctor_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    return SlotsOut(
        doctor_id=doctor_id,
        day=day,
        timezone=settings.CLINIC_TIMEZONE,
        slots=available_slots(db, doctor_id, day),
    )
