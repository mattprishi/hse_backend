from fastapi import APIRouter, Depends, HTTPException, status
from models.predict import SimplePredictInDto, PredictOutDto
from services.predict import PredictionService
from errors import AdNotFoundError

router = APIRouter()


def get_prediction_service() -> PredictionService:
    from main import get_app_state
    return get_app_state().prediction_service


@router.post('/simple_predict', status_code=status.HTTP_200_OK, response_model=PredictOutDto)
async def simple_predict(
    dto: SimplePredictInDto,
    service: PredictionService = Depends(get_prediction_service)
) -> PredictOutDto:
    try:
        return await service.predict_by_item_id(dto.item_id)
    except AdNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
