import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository


@pytest.mark.asyncio
async def test_async_predict_endpoint(app_client: AsyncClient, test_user):
    ad_repo = AdRepository()
    
    ad = await ad_repo.create(
        user_id=test_user.id,
        title="Test Ad",
        description="Test description",
        category=1,
        images_qty=2,
        price=100.0
    )

    with patch("routers.moderation.kafka_client.send_moderation_request", new_callable=AsyncMock) as mock_send:
        response = await app_client.post("/async_predict", params={"item_id": ad.id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "task_id" in data
        mock_send.assert_called_once_with(ad.id)


@pytest.mark.asyncio
async def test_async_predict_not_found(app_client: AsyncClient):
    response = await app_client.post("/async_predict", params={"item_id": 99999})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_moderation_result_pending(app_client: AsyncClient, test_user):
    ad_repo = AdRepository()
    moderation_repo = ModerationResultRepository()
    
    ad = await ad_repo.create(
        user_id=test_user.id,
        title="Test Ad",
        description="Test description",
        category=1,
        images_qty=2,
        price=100.0
    )

    task = await moderation_repo.create(ad.id)

    response = await app_client.get(f"/moderation_result/{task.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task.id
    assert data["status"] == "pending"
    assert data["is_violation"] is None
    assert data["probability"] is None


@pytest.mark.asyncio
async def test_get_moderation_result_not_found(app_client: AsyncClient):
    response = await app_client.get("/moderation_result/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dlq_logic():
    from clients.kafka import KafkaClient
    
    mock_producer = AsyncMock()
    kafka_client = KafkaClient()
    kafka_client.producer = mock_producer
    
    original_msg = {"item_id": 1, "timestamp": "2025-01-01T00:00:00"}
    error_msg = "Test Error"
    
    await kafka_client.send_to_dlq(original_msg, error_msg, retry_count=3)
    
    mock_producer.send_and_wait.assert_called_once()
    call_args = mock_producer.send_and_wait.call_args
    assert call_args[0][0] == "moderation_dlq"
    assert b"Test Error" in call_args[0][1]
