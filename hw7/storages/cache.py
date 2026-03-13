from dataclasses import dataclass
from typing import Any, Mapping, Optional
from clients.redis import get_redis_connection
import json
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisCacheStorage:
    default_ttl: int = 60

    async def get_prediction(self, item_id: int) -> Optional[Mapping[str, Any]]:
        try:
            key = f"prediction:{item_id}"
            async with get_redis_connection() as conn:
                data = await conn.get(key)
                return json.loads(data) if data else None
        except Exception as e:
            logger.warning("Cache get failed: %s", e)
            return None

    async def set_prediction(self, item_id: int, value: Mapping[str, Any]) -> None:
        try:
            key = f"prediction:{item_id}"
            async with get_redis_connection() as conn:
                await conn.setex(
                    name=key,
                    time=self.default_ttl,
                    value=json.dumps(value)
                )
        except Exception as e:
            logger.warning("Cache set failed: %s", e)

    async def delete_prediction(self, item_id: int) -> None:
        try:
            key = f"prediction:{item_id}"
            async with get_redis_connection() as conn:
                await conn.delete(key)
        except Exception as e:
            logger.warning("Cache delete failed: %s", e)
