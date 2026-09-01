from collections.abc import AsyncIterator
from typing import cast

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.db.redis import get_redis
from app.main import app

pytestmark = pytest.mark.integration


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_returns_503_when_redis_is_unavailable(
    client: AsyncClient,
) -> None:
    class UnavailableRedis:
        async def ping(self) -> bool:
            raise RedisConnectionError

    async def override_get_redis() -> AsyncIterator[Redis]:
        yield cast(Redis, UnavailableRedis())

    app.dependency_overrides[get_redis] = override_get_redis

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable"}
