import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Determine active database engine
is_postgres = settings.DATABASE_URL.startswith("postgresql")

try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
except Exception as e:
    logger.warning(f"Failed to create engine for {settings.DATABASE_URL}: {e}. Falling back to SQLite.")
    engine = create_async_engine(
        settings.FALLBACK_SQLITE_URL,
        echo=False,
        future=True,
    )
    is_postgres = False

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
