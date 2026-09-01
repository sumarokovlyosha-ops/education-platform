from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.config import get_redis_settings

redis_settings = get_redis_settings()

redis_client = Redis(
    host=redis_settings.host,
    port=redis_settings.port,
    db=redis_settings.db,
    password=(
        redis_settings.password.get_secret_value()
        if redis_settings.password is not None
        else None
    ),
    decode_responses=True,
    socket_connect_timeout=redis_settings.socket_connect_timeout,
    socket_timeout=redis_settings.socket_timeout,
    health_check_interval=30,
)


async def get_redis() -> AsyncIterator[Redis]:
    yield redis_client
