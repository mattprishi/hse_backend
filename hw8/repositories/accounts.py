from dataclasses import dataclass
from typing import Optional
from clients.postgres import get_pg_connection
from metrics import DB_QUERY_DURATION
from models.entities import Account
from auth import hash_password


@dataclass(frozen=True)
class AccountRepository:
    async def create(self, login: str, password: str) -> Account:
        query = "INSERT INTO account (login, password) VALUES ($1, $2) RETURNING id, login, password, is_blocked"
        hashed = hash_password(password)
        async with get_pg_connection() as conn:
            with DB_QUERY_DURATION.labels(query_type="insert").time():
                row = await conn.fetchrow(query, login, hashed)
            return Account(**dict(row))

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        query = "SELECT id, login, password, is_blocked FROM account WHERE id = $1"
        async with get_pg_connection() as conn:
            with DB_QUERY_DURATION.labels(query_type="select").time():
                row = await conn.fetchrow(query, account_id)
            return Account(**dict(row)) if row else None

    async def delete(self, account_id: int) -> None:
        query = "DELETE FROM account WHERE id = $1"
        async with get_pg_connection() as conn:
            with DB_QUERY_DURATION.labels(query_type="delete").time():
                await conn.execute(query, account_id)

    async def block(self, account_id: int) -> None:
        query = "UPDATE account SET is_blocked = TRUE WHERE id = $1"
        async with get_pg_connection() as conn:
            with DB_QUERY_DURATION.labels(query_type="update").time():
                await conn.execute(query, account_id)

    async def get_by_login_and_password(self, login: str, password: str) -> Optional[Account]:
        hashed = hash_password(password)
        query = "SELECT id, login, password, is_blocked FROM account WHERE login = $1 AND password = $2"
        async with get_pg_connection() as conn:
            with DB_QUERY_DURATION.labels(query_type="select").time():
                row = await conn.fetchrow(query, login, hashed)
            return Account(**dict(row)) if row else None
