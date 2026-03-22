from pydantic import BaseModel, Field


class PredictInDto(BaseModel):
    """Сырые признаки для POST /predict (как в первом ДЗ), без обхода в БД."""

    seller_id: int = Field(ge=1)
    is_verified_seller: bool
    item_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    category: int = Field(ge=0, le=100)
    images_qty: int = Field(ge=0, le=10)


class PredictOutDto(BaseModel):
    is_violation: bool
    probability: float


class SimplePredictInDto(BaseModel):
    item_id: int = Field(ge=1)


class CloseAdInDto(BaseModel):
    item_id: int = Field(ge=1)
