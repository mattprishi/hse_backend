from typing import Generator
import logging
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import asyncpg

import os

from config import DATABASE_URL, MODEL_PATH

logger = logging.getLogger(__name__)
from dependencies import get_prediction_service
from main import app
from repositories.users import UserRepository
from repositories.ads import AdRepository
from repositories.accounts import AccountRepository
from clients.postgres import init_db_pool, close_db_pool
from clients.redis import init_redis_pool, close_redis_pool


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def init_pool(event_loop):
    try:
        await init_db_pool()
        await init_redis_pool()
    except Exception as e:
        pytest.skip(f"Нужны PostgreSQL и Redis (hw8/docker-compose up): {e}")
    yield
    await close_redis_pool()
    await close_db_pool()


@pytest.fixture(scope="session")
async def init_prediction_overrides(init_pool):
    """Подменяет get_prediction_service через dependency_overrides (без записи в app.state)."""
    from ml.model import load_or_train_model
    from services.predict import PredictionService
    from clients.kafka import kafka_client

    model = load_or_train_model(MODEL_PATH)
    svc = PredictionService(model=model)

    def override_prediction() -> PredictionService:
        return svc

    app.dependency_overrides[get_prediction_service] = override_prediction
    try:
        await kafka_client.start()
    except Exception as e:
        logger.warning("Kafka producer not started in tests: %s", e)
    yield
    try:
        await kafka_client.stop()
    except Exception as e:
        logger.warning("Kafka producer stop: %s", e)
    app.dependency_overrides.pop(get_prediction_service, None)


@pytest.fixture(scope="session")
async def setup_database(init_pool):
    """Очищает таблицы перед тестами (схема только из migrations/, см. make migrate)."""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "TRUNCATE TABLE account, users RESTART IDENTITY CASCADE"
    )
    await conn.close()
    yield


@pytest.fixture(scope="session")
async def app_client(init_prediction_overrides, setup_database) -> Generator[AsyncClient, None, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_repository(init_pool) -> UserRepository:
    return UserRepository()


@pytest.fixture
def ad_repository(init_pool) -> AdRepository:
    return AdRepository()


@pytest.fixture
def account_repository(init_pool) -> AccountRepository:
    return AccountRepository()


@pytest.fixture
async def test_account(account_repository: AccountRepository, setup_database):
    login = f"testuser_{os.urandom(4).hex()}"
    acc = await account_repository.create(login, "testpass")
    return {"login": login, "password": "testpass", "id": acc.id}


@pytest.fixture
async def app_client_logged_in(init_prediction_overrides, setup_database, test_account):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/login", json={"login": test_account["login"], "password": test_account["password"]})
        yield client


@pytest.fixture
async def test_user(user_repository: UserRepository, setup_database):
    """Создает тестового пользователя"""
    user = await user_repository.create(
        name="Test User",
        email=f"test_{os.urandom(4).hex()}@example.com",
        is_verified=False
    )
    return user


@pytest.fixture
async def verified_user(user_repository: UserRepository, setup_database):
    """Создает верифицированного пользователя"""
    user = await user_repository.create(
        name="Verified User",
        email=f"verified_{os.urandom(4).hex()}@example.com",
        is_verified=True
    )
    return user
