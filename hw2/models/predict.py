from pydantic import BaseModel, Field


class PredictInDto(BaseModel):
    seller_id: int = Field(ge=0)
    is_verified_seller: bool
    item_id: int = Field(ge=0)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: int = Field(ge=0, le=100)
    images_qty: int = Field(ge=0, le=10)


class PredictOutDto(BaseModel):
    is_violation: bool
    probability: float
