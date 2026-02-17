from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.base import OrmModel

from app.models.user import UserRole


class UserCreate(BaseModel):
    display_name: str
    email: EmailStr
    role: UserRole = UserRole.EDITOR


class UserResponse(OrmModel):
    id: str
    display_name: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
