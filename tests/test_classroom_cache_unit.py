from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.cache.classroom import ClassroomCache

pytestmark = pytest.mark.unit


async def test_get_classrooms_returns_miss_when_redis_fails() -> None:
    school_id = uuid4()
    redis_mock = AsyncMock()
    redis_mock.get.side_effect = RedisConnectionError("Redis is unavailable")
    cache = ClassroomCache(cast(Redis, redis_mock))

    result = await cache.get_school_classrooms(
        school_id=school_id,
        limit=10,
        offset=0,
    )

    assert result.classrooms is None
    assert result.generation is None
    redis_mock.get.assert_awaited_once_with(cache._generation_key(school_id))


async def test_get_classrooms_deletes_invalid_payload() -> None:
    school_id = uuid4()
    redis_mock = AsyncMock()
    redis_mock.get.side_effect = ["4", "not valid json"]
    cache = ClassroomCache(cast(Redis, redis_mock))

    result = await cache.get_school_classrooms(
        school_id=school_id,
        limit=10,
        offset=0,
    )

    expected_key = cache._list_key(
        school_id=school_id,
        generation="4",
        limit=10,
        offset=0,
    )

    assert result.classrooms is None
    assert result.generation == "4"
    redis_mock.delete.assert_awaited_once_with(expected_key)
