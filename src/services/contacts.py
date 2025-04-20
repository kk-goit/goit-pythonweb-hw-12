from pydantic import EmailStr

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.contacts import ContactsRepository
from src.schemas.contacts import ContactsSchema, ContactsUpdateSchema


class ContactsService:
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize the ContactsService with a database session and user.

        Args:
            db (AsyncSession): The SQLAlchemy asynchronous session for database operations.
            user (User): The User object representing the owner of the contacts.
        """
        
        self.repository = ContactsRepository(db, user)

    async def create_contact(self, body: ContactsSchema):
        """
        Create a new contact.

        Args:
            body (ContactsSchema): The contact's data.

        Returns:
            Contact: The newly created contact.
        """
        return await self.repository.create_contact(body)

    async def get_contacts(
        self,
        limit: int,
        offset: int,
        first_name: str = None,
        last_name: str = None,
        email: EmailStr = None,
    ):
        """
        Retrieve contacts from the database that match the given parameters.

        Args:
            limit (int): The number of contacts to retrieve.
            offset (int): The offset of the contacts to retrieve.
            first_name (str, optional): The first name of the contacts to retrieve. Defaults to None.
            last_name (str, optional): The last name of the contacts to retrieve. Defaults to None.
            email (EmailStr, optional): The email address of the contacts to retrieve. Defaults to None.

        Returns:
            Sequence[Contact]: A list of contacts that match the given parameters.
        """
        return await self.repository.get_contacts(
            limit, offset, first_name, last_name, email
        )

    async def get_contact(self, cnt_id: int):
        """
        Retrieve a contact by its ID from the database.

        Args:
            cnt_id (int): The ID of the contact to retrieve.

        Returns:
            Contact | None: The contact with the given ID, or None if not found.
        """
        return await self.repository.get_contact_by_id(cnt_id)

    async def update_contact(self, cnt_id: int, body: ContactsUpdateSchema):
        """
        Update an existing contact by its ID with the provided data.

        Args:
            cnt_id (int): The ID of the contact to update.
            body (ContactsUpdateSchema): The data to update the contact with.

        Returns:
            Contact | None: The updated contact, or None if not found.
        """
        return await self.repository.update_contact(cnt_id, body)

    async def remove_contact(self, cnt_id: int):
        """
        Delete a contact by its ID from the database.

        Args:
            cnt_id (int): The ID of the contact to delete.

        Returns:
            Contact | None: The deleted contact, or None if not found.
        """
        return await self.repository.remove_contact(cnt_id)

    async def get_contacts_upcoming_birthdays(self, days: int, limit: int, offset: int):
        """
        Retrieve a list of contacts with upcoming birthdays within a given number of days.

        Args:
            days (int): The number of days to retrieve contacts with upcoming birthdays.
            limit (int): The maximum number of contacts to retrieve.
            offset (int): The offset of contacts to retrieve.

        Returns:
            list[Contact]: A list of contacts with upcoming birthdays.
        """
        return await self.repository.get_contacts_upcoming_birthdays(
            days, limit, offset
        )
