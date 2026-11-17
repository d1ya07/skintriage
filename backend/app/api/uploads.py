from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.upload import ImageUploadOut
from app.services import storage

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/images", response_model=ImageUploadOut, status_code=status.HTTP_201_CREATED)
def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.patient)),
):
    data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)  # +1 so oversize files are detected
    stored, _ = storage.save_image(user.id, data)
    return ImageUploadOut(
        path=stored.path,
        url=f"/api/uploads/images/{stored.path}",
        width=stored.width,
        height=stored.height,
        size_bytes=stored.size_bytes,
    )


@router.get("/images/{user_id}/{filename}")
def get_image(user_id: int, filename: str, user: User = Depends(get_current_user)):
    # Patients may only see their own images; doctors and admins may see any.
    if user.role == UserRole.patient and user.id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    f = storage.resolve_image(f"{user_id}/{filename}")
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})
