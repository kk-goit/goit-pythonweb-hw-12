import logging

from typing import Optional
from pydantic import EmailStr

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.utils.depended_services import get_authorized_user
from src.services.contacts import ContactsService
from src.schemas.contacts import ContactsSchema, ContactsUpdateSchema, ContactsResponse

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactsResponse])
async def get_contacts(
    limit: int = Query(10, ge=10, le=500),
    offset: int = Query(0, ge=0),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[EmailStr] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    return await service.get_contacts(limit, offset, first_name, last_name, email)


@router.get(
    "/{cnt_id}",
    response_model=ContactsResponse,
    name="Get Contact by id",
    description="Get Contact by id",
    response_description="Contact details",
)
async def get_contact(
    cnt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    contact = await service.get_contact(cnt_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with id: {cnt_id} not found",
        )
    return contact


@router.post(
    "/",
    response_model=ContactsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    body: ContactsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    return await service.create_contact(body)


@router.put("/{cnt_id}", response_model=ContactsResponse)
async def update_contact(
    cnt_id: int,
    body: ContactsUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    contact = await service.update_contact(cnt_id, body)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with id: {cnt_id} not found",
        )
    return contact


@router.delete("/{cnt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    cnt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    await service.remove_contact(cnt_id)
    return None


@router.get("/birthdays/{days}", response_model=list[ContactsResponse])
async def upcoming_birthdays(
    days: int = Path(..., gt=0, lt=365),
    limit: int = Query(10, ge=10, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    service = ContactsService(db, user)
    return await service.get_contacts_upcoming_birthdays(days, limit, offset)
