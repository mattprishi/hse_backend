from fastapi import APIRouter, Depends, HTTPException, status
from repositories.moderation_results import ModerationResultRepository
from repositories.ads import AdRepository
from models.moderation import AsyncPredictResponse, ModerationResultResponse
from clients.kafka import kafka_client
from errors import AdNotFoundError

router = APIRouter()


@router.post("/async_predict", response_model=AsyncPredictResponse)
async def create_moderation_task(item_id: int):
    moderation_repo = ModerationResultRepository()

    try:
        await kafka_client.send_moderation_request(item_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue moderation task"
        )

    return AsyncPredictResponse(
        task_id=0,
        status="pending",
        message="Moderation request accepted"
    )


@router.get("/moderation_result/{task_id}", response_model=ModerationResultResponse)
async def get_moderation_result(task_id: int):
    moderation_repo = ModerationResultRepository()
    task = await moderation_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    response = ModerationResultResponse(
        task_id=task.id,
        status=task.status,
        is_violation=task.is_violation,
        probability=task.probability
    )

    if task.status == "failed":
        response.error = task.error_message

    return response
