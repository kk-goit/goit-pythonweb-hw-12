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
    """
    Get a list of contacts filtered by optional parameters.

    Args:
        limit (int): The maximum number of contacts to retrieve. Defaults to 10.
        offset (int): The offset of contacts to retrieve. Defaults to 0.
        first_name (str): The first name of the contacts to retrieve. Defaults to None.
        last_name (str): The last name of the contacts to retrieve. Defaults to None.
        email (EmailStr): The email of the contacts to retrieve. Defaults to None.

    Returns:
        list[ContactsResponse]: A list of contacts filtered by the given parameters.
    """
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
    """
    Retrieve a contact by its ID from the database.

    Args:
        cnt_id (int): The ID of the contact to retrieve.

    Returns:
        ContactsResponse: The contact with the given ID, or raises an HTTPException
            with a 404 status code if not found.
    """
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
    """
    Create a new contact.

    Args:
        body (ContactsSchema): The contact's data.

    Returns:
        ContactsResponse: The newly created contact.
    """
    service = ContactsService(db, user)
    return await service.create_contact(body)


@router.put("/{cnt_id}", response_model=ContactsResponse)
async def update_contact(
    cnt_id: int,
    body: ContactsUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authorized_user),
):
    """
    Update a contact by its ID.

    Args:
        cnt_id (int): The ID of the contact to update.
        body (ContactsUpdateSchema): The data to update the contact with.

    Returns:
        ContactsResponse: The updated contact.

    Raises:
        HTTPException: If the contact with the given ID is not found.
    """
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
    """
    Delete a contact by its ID.

    Args:
        cnt_id (int): The ID of the contact to delete.

    Returns:
        None

    Raises:
        HTTPException: If the contact with the given ID is not found.
    """
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
    """
    Retrieve a list of contacts that have an upcoming birthday within the specified number of days.

    Args:
        days (int): The number of days to retrieve contacts with upcoming birthdays.
        limit (int): The maximum number of contacts to retrieve. Defaults to 10.
        offset (int): The offset of contacts to retrieve. Defaults to 0.

    Returns:
        list[ContactsResponse]: A list of contacts with upcoming birthdays.
    """
    service = ContactsService(db, user)
    return await service.get_contacts_upcoming_birthdays(days, limit, offset)
