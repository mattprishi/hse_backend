from pydantic import BaseModel, Field


class PredictOutDto(BaseModel):
    is_violation: bool
    probability: float


class SimplePredictInDto(BaseModel):
    item_id: int = Field(ge=1)
