from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_database_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app

database_settings = get_database_settings()

test_database_url = URL.create(
    drivername="postgresql+asyncpg",
    username=database_settings.user,
    password=database_settings.password.get_secret_value(),
    host=database_settings.host,
    port=database_settings.port,
    database="education_platform_test",
)

test_engine = create_async_engine(test_database_url)

test_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind = connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)

    async with AsyncClient (transport=transport,base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def created_user(client: AsyncClient) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "full_name": "Created User",
            "password": "password123",
        }
    )

    assert response.status_code == 201
    return response.json()