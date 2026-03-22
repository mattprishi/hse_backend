from dataclasses import dataclass

from clients.kafka import KafkaClient
from models.moderation import AsyncPredictResponse, ModerationResultResponse
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from errors import AdNotFoundError, ModerationEnqueueFailedError, ModerationTaskNotFoundError


@dataclass(frozen=True)
class ModerationService:
    ad_repository: AdRepository
    moderation_result_repository: ModerationResultRepository
    kafka: KafkaClient

    async def enqueue_moderation(self, item_id: int) -> AsyncPredictResponse:
        ad = await self.ad_repository.get_by_id(item_id)
        if not ad:
            raise AdNotFoundError(f"Ad with id {item_id} not found")

        task = await self.moderation_result_repository.create(item_id)

        try:
            await self.kafka.send_moderation_request(item_id)
        except Exception as e:
            await self.moderation_result_repository.update_result(
                item_id,
                "failed",
                error_message="Failed to queue moderation task",
            )
            raise ModerationEnqueueFailedError() from e

        return AsyncPredictResponse(
            task_id=task.id,
            status="pending",
            message="Moderation request accepted",
        )

    async def get_moderation_result(self, task_id: int) -> ModerationResultResponse:
        task = await self.moderation_result_repository.get_by_id(task_id)
        if not task:
            raise ModerationTaskNotFoundError(task_id)

        response = ModerationResultResponse(
            task_id=task.id,
            status=task.status,
            is_violation=task.is_violation,
            probability=task.probability,
        )
        if task.status == "failed":
            response.error = task.error_message
        return response
