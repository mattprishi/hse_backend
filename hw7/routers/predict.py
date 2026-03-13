from fastapi import APIRouter, Depends, HTTPException, status
import sentry_sdk
from models.predict import SimplePredictInDto, PredictOutDto
from models.entities import Account
from services.predict import PredictionService
from errors import AdNotFoundError
from dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()


def get_prediction_service() -> PredictionService:
    from main import get_app_state
    return get_app_state().prediction_service


@router.post('/simple_predict', status_code=status.HTTP_200_OK, response_model=PredictOutDto)
async def simple_predict(
    dto: SimplePredictInDto,
    current_user: Account = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictOutDto:
    try:
        return await service.predict_by_item_id(dto.item_id)
    except AdNotFoundError as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


class CloseAdInDto(BaseModel):
    item_id: int


@router.post('/close', status_code=status.HTTP_200_OK)
async def close_ad(
    dto: CloseAdInDto,
    current_user: Account = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    closed = await service.close_ad(dto.item_id)
    if not closed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found or already closed")
    return {"status": "ok", "message": f"Ad {dto.item_id} closed"}
