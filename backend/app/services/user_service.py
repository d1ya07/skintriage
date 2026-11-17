from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User, UserRole
from app.schemas.user import UserCreate


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, data: UserCreate, role: UserRole = UserRole.patient) -> User:
    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=role,
        skin_type=data.skin_type,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    user = get_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
