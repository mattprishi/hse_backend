import pytest
from storages.cache import RedisCacheStorage


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_storage_set_and_get(init_pool):
    """Интеграционный тест: проверка записи и чтения из Redis"""
    storage = RedisCacheStorage()
    item_id = 999
    prediction_data = {"is_violation": True, "probability": 0.85}

    await storage.set_prediction(item_id, prediction_data)
    result = await storage.get_prediction(item_id)

    assert result is not None
    assert result["is_violation"] is True
    assert result["probability"] == 0.85


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_storage_get_nonexistent(init_pool):
    """Интеграционный тест: проверка получения несуществующего ключа"""
    storage = RedisCacheStorage()
    result = await storage.get_prediction(88888)

    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_storage_delete(init_pool):
    """Интеграционный тест: проверка удаления из Redis"""
    storage = RedisCacheStorage()
    item_id = 777
    prediction_data = {"is_violation": False, "probability": 0.15}

    await storage.set_prediction(item_id, prediction_data)
    await storage.delete_prediction(item_id)
    result = await storage.get_prediction(item_id)

    assert result is None
