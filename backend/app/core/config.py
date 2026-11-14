from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="Housing Society CMS")
    API_V1_PREFIX: str = Field(default="/api/v1")
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    APP_TIMEZONE: str = Field(default="Asia/Karachi")
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        description="Async PostgreSQL connection URL for FastAPI runtime"
    )
    DATABASE_MIGRATION_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        description="Sync PostgreSQL connection URL for Alembic migrations"
    )
    DATABASE_POOL_SIZE: int = Field(default=5)
    DATABASE_MAX_OVERFLOW: int = Field(default=5)

    # Supabase Auth
    SUPABASE_URL: str = Field(default="https://localhost.supabase.co")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")
    SUPABASE_JWKS_URL: str = Field(default="")
    SUPABASE_JWT_ISSUER: str = Field(default="")
    SUPABASE_JWT_AUDIENCE: str = Field(default="authenticated")

    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000")

    # Supabase Storage Bucket
    SUPABASE_STORAGE_BUCKET: str = Field(default="complaint-attachments")

    # System Operational Parameters
    DUE_SOON_HOURS: int = Field(default=24)
    RECURRING_FAULT_DAYS: int = Field(default=90)

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
