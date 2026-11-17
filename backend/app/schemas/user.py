from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    skin_type: Optional[str] = Field(default=None, max_length=50)

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_bytes(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    skin_type: Optional[str]
    created_at: datetime


class UserAdminUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
