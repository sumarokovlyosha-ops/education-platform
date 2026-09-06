import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import TypeAdapter, ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_redis_settings
from app.schemas.classroom import ClassroomRead

logger = logging.getLogger(__name__)

classroom_list_adapter = TypeAdapter(list[ClassroomRead])


@dataclass(frozen=True)
class ClassroomListCacheResult:
    classrooms: list[ClassroomRead] | None
    generation: str | None


class ClassroomCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.ttl_seconds = get_redis_settings().classroom_cache_ttl_seconds

    @staticmethod
    def _generation_key(school_id: UUID) -> str:
        return f"classrooms:school:{school_id}:generation"

    @staticmethod
    def _list_key(
        school_id: UUID,
        generation: str,
        limit: int,
        offset: int,
    ) -> str:
        return f"classrooms:school:{school_id}:generation:{generation}:limit:{limit}:offset:{offset}"

    async def get_school_classrooms(
        self,
        school_id: UUID,
        limit: int,
        offset: int,
    ) -> ClassroomListCacheResult:
        try:
            raw_generation = await self.redis.get(
                self._generation_key(school_id),
            )

            generation = (
                raw_generation.decode("utf-8")
                if isinstance(raw_generation, bytes)
                else raw_generation
            ) or "0"
            key = self._list_key(
                school_id=school_id,
                generation=generation,
                limit=limit,
                offset=offset,
            )
            payload = await self.redis.get(key)
        except RedisError:
            logger.exception("Failed to read classroom list from Redis")

            return ClassroomListCacheResult(classrooms=None, generation=None)

        if payload is None:
            return ClassroomListCacheResult(classrooms=None, generation=generation)

        try:
            classrooms = classroom_list_adapter.validate_json(payload)
        except ValidationError:
            logger.warning("Invalid classroom list payload in Redis")

            try:
                await self.redis.delete(key)
            except RedisError:
                logger.exception("Failed to delete invalid classroom cache entry")

            return ClassroomListCacheResult(classrooms=None, generation=generation)
        return ClassroomListCacheResult(classrooms=classrooms, generation=generation)

    async def set_school_classrooms(
        self,
        school_id: UUID,
        generation: str,
        limit: int,
        offset: int,
        classrooms: list[ClassroomRead],
    ) -> None:
        try:
            key = self._list_key(
                school_id=school_id,
                generation=generation,
                limit=limit,
                offset=offset,
            )

            payload = classroom_list_adapter.dump_json(classrooms)

            await self.redis.set(
                key,
                payload,
                ex=self.ttl_seconds,
            )
        except RedisError:
            logger.exception("Failed to write classroom list to Redis")

    async def invalidate_school_classrooms(
        self,
        school_id: UUID,
    ) -> None:
        try:
            await self.redis.incr(self._generation_key(school_id))
        except RedisError:
            logger.exception("Failed to invalidate classroom list cache")
