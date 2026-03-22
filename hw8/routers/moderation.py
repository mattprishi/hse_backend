from fastapi import APIRouter, Depends, HTTPException, status
import sentry_sdk
from models.moderation import AsyncPredictResponse, ModerationResultResponse
from services.moderation import ModerationService
from dependencies import get_moderation_service
from errors import AdNotFoundError, ModerationEnqueueFailedError, ModerationTaskNotFoundError

router = APIRouter()


@router.post("/async_predict", response_model=AsyncPredictResponse)
async def create_moderation_task(
    item_id: int,
    service: ModerationService = Depends(get_moderation_service),
):
    try:
        return await service.enqueue_moderation(item_id)
    except AdNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ModerationEnqueueFailedError as e:
        sentry_sdk.capture_exception(e.__cause__ if e.__cause__ else e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue moderation task",
        )


@router.get("/moderation_result/{task_id}", response_model=ModerationResultResponse)
async def get_moderation_result(
    task_id: int,
    service: ModerationService = Depends(get_moderation_service),
):
    try:
        return await service.get_moderation_result(task_id)
    except ModerationTaskNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {e.task_id} not found",
        )
