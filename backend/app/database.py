from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL
# Automatically normalize sync URL scheme to asyncpg if user pasted standard postgresql://
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# If placeholder password is still in .env or localhost default, fallback to local SQLite for instant UI smoke testing
if "[YOUR-PASSWORD]" in db_url or (db_url == "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"):
    db_url = "sqlite+aiosqlite:///./society_local_dev.db"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine_kwargs = {
    "echo": (settings.LOG_LEVEL == "DEBUG"),
    "connect_args": connect_args,
}
if not db_url.startswith("sqlite"):
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_ready() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
