from dataclasses import dataclass
from typing import Mapping, Any, Optional
from clients.postgres import get_pg_connection
from models.entities import User


@dataclass(frozen=True)
class UserRepository:
    async def create(self, name: str, email: str, is_verified: bool = False) -> User:
        query = """
            INSERT INTO users (name, email, is_verified)
            VALUES ($1, $2, $3)
            RETURNING *
        """
        
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, name, email, is_verified)
            return User(**dict(row))
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        query = "SELECT * FROM users WHERE id = $1"
        
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, user_id)
            return User(**dict(row)) if row else None
