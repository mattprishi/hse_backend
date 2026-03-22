import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from models.predict import PredictInDto
from services.predict import PredictionService
from errors import PredictionError


@pytest.mark.asyncio
async def test_predict_cache_hit():
    """Юнит-тест: проверяет, что при наличии данных в кэше не идет запрос в БД"""
    mock_model = MagicMock()
    
    with patch('services.predict.RedisCacheStorage') as MockCache, \
         patch('services.predict.AdRepository') as MockRepo:
        
        mock_cache = MockCache.return_value
        mock_cache.get_prediction = AsyncMock(return_value={"is_violation": True, "probability": 0.9})
        
        mock_repo = MockRepo.return_value
        mock_repo.get_with_user = AsyncMock()
        
        service = PredictionService(model=mock_model, cache_storage=mock_cache, ad_repository=mock_repo)

        result = await service.predict_by_item_id(123)

        assert result.is_violation is True
        assert result.probability == 0.9
        mock_cache.get_prediction.assert_called_once_with(123)
        mock_repo.get_with_user.assert_not_called()


@pytest.mark.asyncio
async def test_predict_cache_miss():
    """Юнит-тест: проверяет, что при отсутствии данных в кэше идет запрос в БД и запись в кэш"""
    mock_model = MagicMock()
    mock_model.predict.return_value = [1]
    mock_model.predict_proba.return_value = [[0.1, 0.9]]
    
    with patch('services.predict.RedisCacheStorage') as MockCache, \
         patch('services.predict.AdRepository') as MockRepo, \
         patch('services.predict.PREDICTION_DURATION') as mock_duration, \
         patch('services.predict.observe_prediction_metrics') as mock_prediction_metrics:
        
        mock_cache = MockCache.return_value
        mock_cache.get_prediction = AsyncMock(return_value=None)
        mock_cache.set_prediction = AsyncMock()
        
        mock_repo = MockRepo.return_value
        mock_repo.get_with_user = AsyncMock(return_value={
            'is_verified_seller': True,
            'images_qty': 5,
            'description': 'Test description',
            'category': 50
        })
        
        service = PredictionService(model=mock_model, cache_storage=mock_cache, ad_repository=mock_repo)

        result = await service.predict_by_item_id(123)

        assert result.is_violation is True
        assert result.probability == 0.9
        mock_cache.get_prediction.assert_called_once_with(123)
        mock_repo.get_with_user.assert_called_once_with(123)
        mock_cache.set_prediction.assert_called_once()
        mock_duration.observe.assert_called_once()
        mock_prediction_metrics.assert_called_once_with(True, 0.9)


@pytest.mark.asyncio
async def test_predict_model_unavailable_updates_metric():
    service = PredictionService(model=None)

    with patch("services.predict.PREDICTION_ERRORS_TOTAL") as mock_errors:
        with pytest.raises(PredictionError, match="Model not loaded"):
            await service.predict_by_item_id(123)

    mock_errors.labels.assert_called_once_with(error_type="model_unavailable")


@pytest.mark.asyncio
async def test_predict_from_dto():
    mock_model = MagicMock()
    mock_model.predict.return_value = [1]
    mock_model.predict_proba.return_value = [[0.2, 0.8]]
    dto = PredictInDto(
        seller_id=1,
        is_verified_seller=False,
        item_id=2,
        name="Ad",
        description="Some text here",
        category=40,
        images_qty=3,
    )
    with patch("services.predict.PREDICTION_DURATION") as mock_duration, patch(
        "services.predict.observe_prediction_metrics"
    ) as mock_obs:
        service = PredictionService(model=mock_model)
        result = await service.predict_from_dto(dto)
    assert result.is_violation is True
    assert result.probability == 0.8
    mock_duration.observe.assert_called_once()
    mock_obs.assert_called_once_with(True, 0.8)


@pytest.mark.asyncio
async def test_close_ad_invalidates_cache():
    """Юнит-тест: проверяет, что при закрытии объявления инвалидируется кэш"""
    mock_model = MagicMock()
    
    with patch('services.predict.RedisCacheStorage') as MockCache, \
         patch('services.predict.AdRepository') as MockRepo, \
         patch('services.predict.ModerationResultRepository') as MockModeration:
        
        mock_cache = MockCache.return_value
        mock_cache.delete_prediction = AsyncMock()
        
        mock_repo = MockRepo.return_value
        mock_repo.close = AsyncMock(return_value=True)
        
        mock_moderation = MockModeration.return_value
        mock_moderation.delete_by_item_id = AsyncMock()
        
        service = PredictionService(
            model=mock_model,
            cache_storage=mock_cache,
            ad_repository=mock_repo,
            moderation_result_repository=mock_moderation,
        )

        result = await service.close_ad(123)
        
        assert result is True
        mock_repo.close.assert_called_once_with(123)
        mock_cache.delete_prediction.assert_called_once_with(123)
        mock_moderation.delete_by_item_id.assert_called_once_with(123)
