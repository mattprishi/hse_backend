#!/usr/bin/env python3
"""Создаёт одного пользователя и одно объявление в БД для проверки /simple_predict. Запуск: DATABASE_URL=... python create_user_and_ad.py"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.users import UserRepository
from repositories.ads import AdRepository
from clients.postgres import init_db_pool, close_db_pool


async def main():
    await init_db_pool()
    user_repo = UserRepository()
    ad_repo = AdRepository()
    user = await user_repo.create("Manual Test User", "manual@test.example", is_verified=True)
    ad = await ad_repo.create(
        user_id=user.id,
        title="Test ad for predict",
        description="Description for manual test",
        category=50,
        images_qty=5,
        price=1000.0,
    )
    await close_db_pool()
    print(f"Created user id={user.id}, ad id={ad.id}")
    print(f"Predict: curl -b cookies.txt -X POST http://localhost:8003/simple_predict -H 'Content-Type: application/json' -d '{{\"item_id\": {ad.id}}}'")


if __name__ == "__main__":
    asyncio.run(main())
