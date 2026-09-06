from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.cache.classroom import ClassroomCache
from app.db.redis import redis_client
from app.schemas.classroom import ClassroomRead

pytestmark = pytest.mark.integration


async def test_classroom_cache_miss_hit_and_invalidation() -> None:
    school_id = uuid4()
    limit = 10
    offset = 0
    now = datetime.now(UTC)

    classroom = ClassroomRead(
        id=uuid4(),
        school_id=school_id,
        name="10A",
        academic_year="2026/2027",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    cache = ClassroomCache(redis_client)

    generation_key = cache._generation_key(school_id)
    cached_list_key = cache._list_key(
        school_id=school_id,
        generation="0",
        limit=limit,
        offset=offset,
    )
    next_list_key = cache._list_key(
        school_id=school_id,
        generation="1",
        limit=limit,
        offset=offset,
    )

    try:
        miss = await cache.get_school_classrooms(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )
        generation = miss.generation

        assert miss.classrooms is None
        assert generation == "0"

        await cache.set_school_classrooms(
            school_id=school_id,
            generation=generation,
            limit=limit,
            offset=offset,
            classrooms=[classroom],
        )

        hit = await cache.get_school_classrooms(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )

        assert hit.classrooms == [classroom]
        assert hit.generation == "0"

        ttl_seconds = await redis_client.ttl(cached_list_key)

        assert 0 < ttl_seconds <= cache.ttl_seconds

        await cache.invalidate_school_classrooms(school_id)

        invalidated = await cache.get_school_classrooms(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )

        assert invalidated.classrooms is None
        assert invalidated.generation == "1"

    finally:
        await redis_client.delete(
            generation_key,
            cached_list_key,
            next_list_key,
        )
