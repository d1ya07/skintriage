from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(user: User) -> Token:
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return Token(
        access_token=create_access_token(user.id, user.role.value),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if user_service.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    return user_service.create_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _issue_token(user)


@router.post("/token", response_model=Token, include_in_schema=True)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Form-based login so the Swagger 'Authorize' button works."""
    user = user_service.authenticate(db, form.username, form.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _issue_token(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: User = Depends(get_current_user)):
    # Stateless JWT: the client deletes its token.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
