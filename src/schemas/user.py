from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.conf import constants
from src.entity.models import UserRole


class UserBase(BaseModel):
    username: str = Field(
        min_length=2, max_length=constants.NAME_MAX_LENGTH, description="Username"
    )
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(
        min_length=constants.PASSWD_MIN_LENGTH,
        max_length=constants.PASSWD_MAX_LENGTH,
        description="Password",
    )


class UserResponse(UserBase):
    id: int
    avatar: str | None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
