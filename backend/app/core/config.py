from functools import lru_cache

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

    # Image uploads
    UPLOAD_DIR: str = "uploads"  # relative paths are resolved from backend/
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
    IMAGE_MAX_SIDE: int = 1024  # stored images are downscaled to this
    IMAGE_MIN_SIDE: int = 128

    # Appointment scheduling
    CLINIC_TIMEZONE: str = "Asia/Kolkata"
    CLINIC_OPEN_HOUR: int = 9
    CLINIC_CLOSE_HOUR: int = 17
    SLOT_MINUTES: int = 30
    BOOKING_WINDOW_DAYS: int = 60

    # FAQ chatbot
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-5-5"
    CHAT_MAX_TOKENS: int = 400
    CHAT_RATE_LIMIT_PER_MINUTE: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
