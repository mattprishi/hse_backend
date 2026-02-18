from pydantic import BaseModel
from datetime import datetime


class User(BaseModel):
    id: int
    name: str
    email: str
    is_verified: bool
    created_at: datetime


class Ad(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    category: int
    images_qty: int
    price: float
    created_at: datetime
