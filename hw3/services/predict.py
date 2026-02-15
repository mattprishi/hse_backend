from dataclasses import dataclass
from models.predict import PredictOutDto
from errors import PredictionError, AdNotFoundError
from repositories.ads import AdRepository
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictionService:
    model: object
    ad_repository: AdRepository = AdRepository()

    async def predict_by_item_id(self, item_id: int) -> PredictOutDto:
        if self.model is None:
            raise PredictionError("Model not loaded")
        
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
        
        features = np.array([[
            1.0 if ad_data['is_verified_seller'] else 0.0,
            ad_data['images_qty'] / 10.0,
            len(ad_data['description']) / 1000.0,
            ad_data['category'] / 100.0,
        ]])
        
        try:
            prediction = int(self.model.predict(features)[0])
            probability = float(self.model.predict_proba(features)[0][1])
            
            is_violation = bool(prediction)
            
            logger.info(
                f"Result for item_id={item_id}: "
                f"is_violation={is_violation}, probability={probability:.4f}"
            )
            
            return PredictOutDto(is_violation=is_violation, probability=probability)
        except Exception as e:
            logger.exception("Prediction error")
            raise PredictionError(f"Prediction failed: {str(e)}")
