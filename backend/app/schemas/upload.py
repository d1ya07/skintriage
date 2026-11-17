from pydantic import BaseModel


class ImageUploadOut(BaseModel):
    path: str
    url: str
    width: int
    height: int
    size_bytes: int
