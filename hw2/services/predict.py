from dataclasses import dataclass
from models.predict import PredictInDto, PredictOutDto
from errors import PredictionError
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictionService:
    model: object = None

    async def predict(self, data: PredictInDto) -> PredictOutDto:
        if self.model is None:
            raise PredictionError("Model not loaded")

        logger.info(
            f"Request: seller_id={data.seller_id}, item_id={data.item_id}, "
            f"is_verified={data.is_verified_seller}, images={data.images_qty}, "
            f"desc_len={len(data.description)}, category={data.category}"
        )

        features = np.array([[
            1.0 if data.is_verified_seller else 0.0,
            data.images_qty / 10.0,
            len(data.description) / 1000.0,
            data.category / 100.0,
        ]])

        try:
            prediction = int(self.model.predict(features)[0])
            probability = float(self.model.predict_proba(features)[0][1])
            
            is_violation = bool(prediction)
            
            logger.info(
                f"Response: is_violation={is_violation}, probability={probability:.4f}"
            )
            
            return PredictOutDto(
                is_violation=is_violation,
                probability=probability
            )
        except Exception as e:
            logger.exception("Prediction error")
            raise PredictionError(f"Prediction failed: {str(e)}")
