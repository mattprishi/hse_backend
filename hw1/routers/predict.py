from fastapi import APIRouter, status
from models.predict import PredictInDto
from services.predict import PredictionService


router = APIRouter()
prediction_service = PredictionService()


@router.post('/predict', status_code=status.HTTP_200_OK, response_model=bool)
async def predict(dto: PredictInDto) -> bool:
    return await prediction_service.predict(dto)


