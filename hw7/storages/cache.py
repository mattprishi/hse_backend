from dataclasses import dataclass
from typing import Any, Mapping, Optional
from clients.redis import get_redis_connection
import json


@dataclass(frozen=True)
class RedisCacheStorage:
    # TTL 60 секунд: баланс между актуальностью и снижением нагрузки на БД.
    # При высокой нагрузке даже минутный кэш снимает тысячи запросов.
    default_ttl: int = 60

    async def get_prediction(self, item_id: int) -> Optional[Mapping[str, Any]]:
        key = f"prediction:{item_id}"
        async with get_redis_connection() as conn:
            data = await conn.get(key)
            return json.loads(data) if data else None

    async def set_prediction(self, item_id: int, value: Mapping[str, Any]) -> None:
        key = f"prediction:{item_id}"
        async with get_redis_connection() as conn:
            await conn.setex(
                name=key,
                time=self.default_ttl,
                value=json.dumps(value)
            )

    async def delete_prediction(self, item_id: int) -> None:
        key = f"prediction:{item_id}"
        async with get_redis_connection() as conn:
            await conn.delete(key)
