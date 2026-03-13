from pydantic import BaseModel, Field
from datetime import datetime


class User(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    is_verified: bool = False
    created_at: datetime


class Ad(BaseModel):
    id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    category: int = Field(..., ge=0, le=100)
    images_qty: int = Field(..., ge=0, le=10)
    price: float = Field(..., ge=0)
    created_at: datetime
    is_closed: bool = False


class Account(BaseModel):
    id: int = Field(..., gt=0)
    login: str
    password: str = ""
    is_blocked: bool = False
