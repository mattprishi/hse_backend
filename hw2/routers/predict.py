from fastapi import APIRouter, status, HTTPException
from models.predict import PredictInDto, PredictOutDto
from services.predict import PredictionService


router = APIRouter()
prediction_service = None


def set_model(model):
    global prediction_service
    prediction_service = PredictionService(model=model)


@router.post('/predict', status_code=status.HTTP_200_OK, response_model=PredictOutDto)
async def predict(dto: PredictInDto) -> PredictOutDto:
    if prediction_service is None or prediction_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return await prediction_service.predict(dto)
