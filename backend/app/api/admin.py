from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models import User, UserRole
from app.schemas.user import UserAdminUpdate, UserOut

admin_only = require_roles(UserRole.admin)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(admin_only),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == current.id and (
        (data.role is not None and data.role != UserRole.admin) or data.is_active is False
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't demote or deactivate yourself")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user
