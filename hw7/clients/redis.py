import redis.asyncio as redis
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from config import REDIS_HOST, REDIS_PORT

_redis_pool: Optional[redis.Redis] = None


async def init_redis_pool():
    global _redis_pool
    _redis_pool = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


async def close_redis_pool():
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


@asynccontextmanager
async def get_redis_connection() -> AsyncGenerator[redis.Redis, None]:
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized")
    yield _redis_pool
