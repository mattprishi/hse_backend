from dataclasses import dataclass
from typing import Mapping, Any, Optional
from clients.postgres import get_pg_connection
from models.entities import Ad


@dataclass(frozen=True)
class AdRepository:
    async def create(
        self,
        user_id: int,
        title: str,
        description: str,
        category: int,
        images_qty: int,
        price: float
    ) -> Ad:
        query = """
            INSERT INTO ads (user_id, title, description, category, images_qty, price)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                query, user_id, title, description, category, images_qty, price
            )
            return Ad(**dict(row))
    
    async def get_by_id(self, ad_id: int) -> Optional[Ad]:
        query = "SELECT * FROM ads WHERE id = $1"
        
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, ad_id)
            return Ad(**dict(row)) if row else None
    
    async def get_with_user(self, ad_id: int) -> Optional[Mapping[str, Any]]:
        query = """
            SELECT 
                a.*,
                u.is_verified as is_verified_seller
            FROM ads a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = $1
        """
        
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(query, ad_id)
            return dict(row) if row else None
