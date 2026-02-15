import pytest
from httpx import AsyncClient
from repositories.ads import AdRepository
from models.entities import User


@pytest.mark.asyncio
async def test_simple_predict_positive(
    app_client: AsyncClient,
    ad_repository: AdRepository,
    test_user: User
):
    """Проверяет положительный результат предсказания (есть нарушение)"""
    # Создаем объявление с признаками нарушения:
    # неверифицированный продавец + мало фото
    ad = await ad_repository.create(
        user_id=test_user.id,
        title="Suspicious Ad",
        description="Short description",
        category=50,
        images_qty=1,
        price=1000.0
    )
    
    response = await app_client.post("/simple_predict", json={"item_id": ad.id})
    
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert 0.0 <= data["probability"] <= 1.0
    assert data["is_violation"] is True  # Ожидаем нарушение


@pytest.mark.asyncio
async def test_simple_predict_negative(
    app_client: AsyncClient,
    ad_repository: AdRepository,
    verified_user: User
):
    """Проверяет отрицательный результат предсказания (нет нарушения)"""
    # Создаем объявление БЕЗ признаков нарушения:
    # верифицированный продавец + много фото
    ad = await ad_repository.create(
        user_id=verified_user.id,
        title="Good Ad",
        description="Very detailed description with lots of information",
        category=75,
        images_qty=8,
        price=5000.0
    )
    
    response = await app_client.post("/simple_predict", json={"item_id": ad.id})
    
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert 0.0 <= data["probability"] <= 1.0
    assert data["is_violation"] is False  # Ожидаем отсутствие нарушения


@pytest.mark.asyncio
async def test_simple_predict_not_found(app_client: AsyncClient):
    """Проверяет ошибку 404 для несуществующего объявления"""
    response = await app_client.post("/simple_predict", json={"item_id": 99999})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_simple_predict_invalid_item_id(app_client: AsyncClient):
    """Проверяет валидацию item_id"""
    response = await app_client.post("/simple_predict", json={"item_id": 0})
    assert response.status_code == 422  # Validation error
