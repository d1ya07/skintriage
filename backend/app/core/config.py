from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SkinTriage API"
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:5173"

    # Image uploads
    UPLOAD_DIR: str = "uploads"  # relative paths are resolved from backend/
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
    IMAGE_MAX_SIDE: int = 1024
    IMAGE_MIN_SIDE: int = 128

    # Appointment scheduling
    CLINIC_TIMEZONE: str = "Asia/Kolkata"
    CLINIC_OPEN_HOUR: int = 9
    CLINIC_CLOSE_HOUR: int = 17
    SLOT_MINUTES: int = 30
    BOOKING_WINDOW_DAYS: int = 60

    # Email notifications
    #   disabled: send nothing | console: print emails to the server log | smtp: really send
    EMAIL_BACKEND: Literal["disabled", "console", "smtp"] = "console"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_STARTTLS: bool = False
    EMAIL_FROM: str = "SkinTriage <no-reply@skintriage.local>"

    # FAQ chatbot
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-5-5"
    CHAT_MAX_TOKENS: int = 400
    CHAT_RATE_LIMIT_PER_MINUTE: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
