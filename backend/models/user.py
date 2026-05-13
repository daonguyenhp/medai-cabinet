from pydantic import BaseModel, Field
from typing import Optional


class UserBase(BaseModel):
    name: str
    age: Optional[int] = None
    caregiver_phone: Optional[str] = None
    device_id: Optional[str] = None


class UserCreate(UserBase):
    user_id: str
    email: Optional[str] = None


class UserResponse(UserBase):
    user_id: str
    email: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
