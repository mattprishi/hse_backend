from dataclasses import dataclass
from time import perf_counter
import sentry_sdk
from models.predict import PredictInDto, PredictOutDto
from errors import PredictionError, AdNotFoundError
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from storages.cache import RedisCacheStorage
from metrics import (
    PREDICTION_DURATION,
    PREDICTION_ERRORS_TOTAL,
    observe_prediction_metrics,
)
import logging

from ml.model import build_feature_row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictionService:
    model: object
    ad_repository: AdRepository = AdRepository()
    cache_storage: RedisCacheStorage = RedisCacheStorage()
    moderation_result_repository: ModerationResultRepository = ModerationResultRepository()

    async def predict_by_item_id(self, item_id: int) -> PredictOutDto:
        if self.model is None:
            PREDICTION_ERRORS_TOTAL.labels(error_type="model_unavailable").inc()
            exc = PredictionError("Model not loaded")
            sentry_sdk.capture_exception(exc)
            raise exc
        
        # Check cache first
        cached = await self.cache_storage.get_prediction(item_id)
        if cached:
            logger.info(f"Cache hit for item_id={item_id}")
            return PredictOutDto(**cached)
        
        logger.info(f"Cache miss for item_id={item_id}")
        
        ad_data = await self.ad_repository.get_with_user(item_id)
        
        if not ad_data:
            raise AdNotFoundError(f"Ad with id {item_id} not found")
        
        logger.info(
            f"Predicting for item_id={item_id}, "
            f"is_verified={ad_data['is_verified_seller']}, "
            f"images={ad_data['images_qty']}, "
            f"desc_len={len(ad_data['description'])}, "
            f"category={ad_data['category']}"
        )

        features = build_feature_row(
            bool(ad_data["is_verified_seller"]),
            int(ad_data["images_qty"]),
            str(ad_data["description"]),
            int(ad_data["category"]),
        )
        
        try:
            started_at = perf_counter()
            prediction = int(self.model.predict(features)[0])
            probability = float(self.model.predict_proba(features)[0][1])
            PREDICTION_DURATION.observe(perf_counter() - started_at)
            
            is_violation = bool(prediction)
            observe_prediction_metrics(is_violation, probability)
            
            logger.info(
                f"Result for item_id={item_id}: "
                f"is_violation={is_violation}, probability={probability:.4f}"
            )
            
            result = PredictOutDto(is_violation=is_violation, probability=probability)
            
            # Save to cache
            await self.cache_storage.set_prediction(item_id, result.model_dump())
            
            return result
        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(error_type="prediction_error").inc()
            logger.exception("Prediction error")
            sentry_sdk.capture_exception(e)
            raise PredictionError(f"Prediction failed: {str(e)}")

    async def predict_from_dto(self, dto: PredictInDto) -> PredictOutDto:
        """Прямой инференс по признакам (без БД и кэша), эндпоинт POST /predict."""
        if self.model is None:
            PREDICTION_ERRORS_TOTAL.labels(error_type="model_unavailable").inc()
            exc = PredictionError("Model not loaded")
            sentry_sdk.capture_exception(exc)
            raise exc

        logger.info(
            "predict /predict: item_id=%s seller_id=%s category=%s",
            dto.item_id,
            dto.seller_id,
            dto.category,
        )
        features = build_feature_row(
            dto.is_verified_seller,
            dto.images_qty,
            dto.description,
            dto.category,
        )
        try:
            started_at = perf_counter()
            prediction = int(self.model.predict(features)[0])
            probability = float(self.model.predict_proba(features)[0][1])
            PREDICTION_DURATION.observe(perf_counter() - started_at)
            is_violation = bool(prediction)
            observe_prediction_metrics(is_violation, probability)
            return PredictOutDto(is_violation=is_violation, probability=probability)
        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(error_type="prediction_error").inc()
            logger.exception("Prediction error (/predict)")
            sentry_sdk.capture_exception(e)
            raise PredictionError(f"Prediction failed: {str(e)}")

    async def close_ad(self, item_id: int) -> bool:
        closed = await self.ad_repository.close(item_id)
        if closed:
            await self.cache_storage.delete_prediction(item_id)
            await self.moderation_result_repository.delete_by_item_id(item_id)
        return closed
