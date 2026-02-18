from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ModerationResult(BaseModel):
    id: int
    item_id: int
    status: str
    is_violation: Optional[bool] = None
    probability: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class AsyncPredictResponse(BaseModel):
    task_id: int
    status: str
    message: str


class ModerationResultResponse(BaseModel):
    task_id: int
    status: str
    is_violation: Optional[bool] = None
    probability: Optional[float] = None
    error: Optional[str] = None
