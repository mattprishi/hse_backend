from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from clients.postgres import get_pg_connection
from models.moderation import ModerationResult


@dataclass(frozen=True)
class ModerationResultRepository:
    async def create(self, item_id: int) -> ModerationResult:
        query = """
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1, 'pending')
            RETURNING *
        """
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, item_id)
            return ModerationResult(**dict(row))

    async def get_by_id(self, task_id: int) -> Optional[ModerationResult]:
        query = "SELECT * FROM moderation_results WHERE id = $1"
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, task_id)
            return ModerationResult(**dict(row)) if row else None

    async def update_result(
        self,
        item_id: int,
        status: str,
        is_violation: Optional[bool] = None,
        probability: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        query = """
            UPDATE moderation_results
            SET status = $1,
                is_violation = $2,
                probability = $3,
                error_message = $4,
                processed_at = NOW()
            WHERE id = (
                SELECT id FROM moderation_results
                WHERE item_id = $5 AND status = 'pending'
                ORDER BY id DESC
                LIMIT 1
            )
        """
        async with get_pg_connection() as conn:
            await conn.execute(
                query, status, is_violation, probability, error_message, item_id
            )
