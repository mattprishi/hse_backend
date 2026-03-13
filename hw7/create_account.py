#!/usr/bin/env python3
"""Создаёт аккаунт в БД (логин/пароль). Запуск: DATABASE_URL=... python create_account.py [login] [password]"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.accounts import AccountRepository
from clients.postgres import init_db_pool, close_db_pool


async def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "testuser"
    password = sys.argv[2] if len(sys.argv) > 2 else "testpass"
    await init_db_pool()
    repo = AccountRepository()
    acc = await repo.create(login, password)
    await close_db_pool()
    print(f"Created account: id={acc.id} login={acc.login}")


if __name__ == "__main__":
    asyncio.run(main())
