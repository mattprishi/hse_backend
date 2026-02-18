from typing import Generator
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import asyncpg

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL, MODEL_PATH
import main as main_module
from main import app, get_app_state
from repositories.users import UserRepository
from repositories.ads import AdRepository
from clients.postgres import init_db_pool, close_db_pool


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_pool(event_loop):
    await init_db_pool()
    yield
    await close_db_pool()


@pytest.fixture(scope="session", autouse=True)
async def init_app_state(init_pool):
    """Инициализирует app state (модель + PredictionService) для тестов API."""
    from model import load_or_train_model
    from services.predict import PredictionService
    from clients.kafka import kafka_client
    model = load_or_train_model(MODEL_PATH)
    main_module._app_state = main_module.AppState(prediction_service=PredictionService(model=model))
    # Kafka будет мокаться в тестах, но можно инициализировать для полноты
    try:
        await kafka_client.start()
    except:
        pass  # Игнорируем ошибки подключения к Kafka в тестах
    yield
    try:
        await kafka_client.stop()
    except:
        pass
    main_module._app_state = None


@pytest.fixture(scope="session", autouse=True)
async def setup_database(init_pool):
    """Очищает таблицы перед тестами"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute("TRUNCATE TABLE moderation_results CASCADE")
    await conn.execute("TRUNCATE TABLE ads CASCADE")
    await conn.execute("TRUNCATE TABLE users CASCADE")
    await conn.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
    await conn.execute("ALTER SEQUENCE ads_id_seq RESTART WITH 1")
    await conn.execute("ALTER SEQUENCE moderation_results_id_seq RESTART WITH 1")
    
    await conn.close()
    yield


@pytest.fixture
async def app_client() -> Generator[AsyncClient, None, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_repository() -> UserRepository:
    return UserRepository()


@pytest.fixture
def ad_repository() -> AdRepository:
    return AdRepository()


@pytest.fixture
async def test_user(user_repository: UserRepository):
    """Создает тестового пользователя"""
    user = await user_repository.create(
        name="Test User",
        email=f"test_{os.urandom(4).hex()}@example.com",
        is_verified=False
    )
    return user


@pytest.fixture
async def verified_user(user_repository: UserRepository):
    """Создает верифицированного пользователя"""
    user = await user_repository.create(
        name="Verified User",
        email=f"verified_{os.urandom(4).hex()}@example.com",
        is_verified=True
    )
    return user
