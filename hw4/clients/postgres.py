import asyncpg
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from config import DATABASE_URL


_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)


async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()


@asynccontextmanager
async def get_pg_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    
    async with _pool.acquire() as connection:
        yield connection
