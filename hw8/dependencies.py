from typing import Optional
from fastapi import Cookie, Depends, HTTPException, Request, status
from models.entities import Account
from services.auth import AuthService
from services.predict import PredictionService
from services.moderation import ModerationService
from repositories.accounts import AccountRepository
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from clients.kafka import KafkaClient, kafka_client


def get_prediction_service(request: Request) -> PredictionService:
    return request.app.state.prediction_service


def get_kafka_client() -> KafkaClient:
    return kafka_client


def get_moderation_service(kafka: KafkaClient = Depends(get_kafka_client)) -> ModerationService:
    return ModerationService(
        ad_repository=AdRepository(),
        moderation_result_repository=ModerationResultRepository(),
        kafka=kafka,
    )


def get_auth_service() -> AuthService:
    return AuthService(account_repository=AccountRepository())


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> Account:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = auth_service.verify_token(access_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        account = await auth_service.account_repository.get_by_id(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not account or account.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked or deleted")
    return account