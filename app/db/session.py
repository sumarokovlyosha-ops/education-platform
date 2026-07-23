from collections.abc import AsyncIterator

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_database_settings


database_settings = get_database_settings()

database_url = URL.create(
    drivername="postgresql+asyncpg",
    username=database_settings.user,
    password=database_settings.password.get_secret_value(),
    host=database_settings.host,
    port=database_settings.port,
    database=database_settings.db,
)

engine: AsyncEngine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
