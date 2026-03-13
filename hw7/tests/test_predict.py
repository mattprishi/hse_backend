import pytest
from httpx import AsyncClient, ASGITransport
from repositories.ads import AdRepository
from models.entities import User
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint(app_client: AsyncClient):
    response = await app_client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "predictions_total" in response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_predict_positive(
    app_client_logged_in: AsyncClient,
    ad_repository: AdRepository,
    test_user: User
):
    """Проверяет положительный результат предсказания (есть нарушение)"""
    ad = await ad_repository.create(
        user_id=test_user.id,
        title="Suspicious Ad",
        description="Short description",
        category=50,
        images_qty=1,
        price=1000.0
    )
    
    response = await app_client_logged_in.post("/simple_predict", json={"item_id": ad.id})
    
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert 0.0 <= data["probability"] <= 1.0
    assert data["is_violation"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_predict_negative(
    app_client_logged_in: AsyncClient,
    ad_repository: AdRepository,
    verified_user: User
):
    """Проверяет отрицательный результат предсказания (нет нарушения)"""
    ad = await ad_repository.create(
        user_id=verified_user.id,
        title="Good Ad",
        description="Very detailed description with lots of information",
        category=75,
        images_qty=8,
        price=5000.0
    )
    
    response = await app_client_logged_in.post("/simple_predict", json={"item_id": ad.id})
    
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert 0.0 <= data["probability"] <= 1.0
    assert data["is_violation"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_predict_not_found(app_client_logged_in: AsyncClient):
    """Проверяет ошибку 404 для несуществующего объявления"""
    response = await app_client_logged_in.post("/simple_predict", json={"item_id": 99999})
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_predict_unauthorized(init_app_state, setup_database):
    """Без токена предсказание возвращает 401"""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/simple_predict", json={"item_id": 1})
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_predict_invalid_item_id(app_client_logged_in: AsyncClient):
    """Проверяет валидацию item_id"""
    response = await app_client_logged_in.post("/simple_predict", json={"item_id": 0})
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_hit(
    app_client_logged_in: AsyncClient,
    ad_repository: AdRepository,
    verified_user: User
):
    """Проверяет работу кэширования при повторном запросе"""
    ad = await ad_repository.create(
        user_id=verified_user.id,
        title="Cached Ad",
        description="Testing cache functionality",
        category=60,
        images_qty=5,
        price=2000.0
    )
    
    response1 = await app_client_logged_in.post("/simple_predict", json={"item_id": ad.id})
    assert response1.status_code == 200
    
    with patch('services.predict.AdRepository.get_with_user') as mock_db:
        response2 = await app_client_logged_in.post("/simple_predict", json={"item_id": ad.id})
        assert response2.status_code == 200
        assert response1.json() == response2.json()
        mock_db.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_ad(
    app_client_logged_in: AsyncClient,
    ad_repository: AdRepository,
    test_user: User
):
    """Проверяет закрытие объявления"""
    ad = await ad_repository.create(
        user_id=test_user.id,
        title="Ad to close",
        description="Will be closed",
        category=40,
        images_qty=3,
        price=1500.0
    )
    
    response = await app_client_logged_in.post("/close", json={"item_id": ad.id})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    predict_response = await app_client_logged_in.post("/simple_predict", json={"item_id": ad.id})
    assert predict_response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_nonexistent_ad(app_client_logged_in: AsyncClient):
    """Проверяет закрытие несуществующего объявления"""
    response = await app_client_logged_in.post("/close", json={"item_id": 99999})
    assert response.status_code == 404
