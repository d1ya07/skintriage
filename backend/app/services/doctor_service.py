from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Doctor, Hospital


def list_doctors(
    db: Session,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
) -> list[Doctor]:
    stmt = (
        select(Doctor)
        .join(Doctor.hospital)
        .options(joinedload(Doctor.hospital))
        .order_by(Doctor.name)
    )
    if specialty:
        stmt = stmt.where(Doctor.specialty.ilike(specialty))
    if city:
        stmt = stmt.where(Hospital.city.ilike(city))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Doctor.name.ilike(like), Doctor.specialty.ilike(like), Hospital.name.ilike(like))
        )
    return list(db.scalars(stmt).all())


def list_specialties(db: Session) -> list[str]:
    return list(db.scalars(select(Doctor.specialty).distinct().order_by(Doctor.specialty)).all())


def list_cities(db: Session) -> list[str]:
    return list(db.scalars(select(Hospital.city).distinct().order_by(Hospital.city)).all())
