from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.conf import constants


class ContactsSchema(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=constants.NAME_MAX_LENGTH,
        description="Contact's first name",
    )
    last_name: str = Field(
        min_length=1,
        max_length=constants.NAME_MAX_LENGTH,
        description="Contact's last name",
    )
    email: Optional[EmailStr] = Field(
        max_length=constants.EMAIL_MAX_LENGTH,
        default=None,
        description="Contact's EMail",
    )
    phone: Optional[int] = Field(
        default=None,
        le=999999999999,
        ge=100000000000,
        description="Contact's phone number, digits only",
    )
    birth_date: date = Field(description="Contact's birth day date")
    description: Optional[str] = Field(
        default=None,
        min_length=constants.DESCRIPTION_MIN_LENGTH,
        max_length=constants.DESCRIPTION_MAX_LENGTH,
        description="Contact's description",
    )


class ContactsUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=constants.NAME_MAX_LENGTH,
        description="Contact's first name",
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=constants.NAME_MAX_LENGTH,
        description="Contact's last name",
    )
    email: Optional[EmailStr] = Field(
        max_length=constants.EMAIL_MAX_LENGTH,
        default=None,
        description="Contact's EMail",
    )
    phone: Optional[int] = Field(
        default=None,
        le=999999999999,
        ge=100000000000,
        description="Contact's phone number, digits only",
    )
    birth_date: Optional[date] = Field(
        default=None, description="Contact's birth day date"
    )
    description: Optional[str] = Field(
        default=None,
        min_length=constants.DESCRIPTION_MIN_LENGTH,
        max_length=constants.DESCRIPTION_MAX_LENGTH,
        description="Contact's description",
    )


class ContactsResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[EmailStr]
    phone: Optional[int]
    birth_date: date
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
