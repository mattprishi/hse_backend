from dataclasses import dataclass
from models.predict import PredictInDto
from errors import PredictionError


@dataclass(frozen=True)
class PredictionService:
    async def predict(self, data: PredictInDto) -> bool:
        if data.category < 0:
            raise PredictionError("Invalid category")

        if data.is_verified_seller:
            return True

        return data.images_qty > 0


