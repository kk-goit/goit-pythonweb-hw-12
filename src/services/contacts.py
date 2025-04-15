from pydantic import EmailStr

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.contacts import ContactsRepository
from src.schemas.contacts import ContactsSchema, ContactsUpdateSchema


class ContactsService:
    def __init__(self, db: AsyncSession, user: User):
        self.repository = ContactsRepository(db, user)

    async def create_contact(self, body: ContactsSchema):
        return await self.repository.create_contact(body)

    async def get_contacts(
        self,
        limit: int,
        offset: int,
        first_name: str = None,
        last_name: str = None,
        email: EmailStr = None,
    ):
        return await self.repository.get_contacts(
            limit, offset, first_name, last_name, email
        )

    async def get_contact(self, cnt_id: int):
        return await self.repository.get_contact_by_id(cnt_id)

    async def update_contact(self, cnt_id: int, body: ContactsUpdateSchema):
        return await self.repository.update_contact(cnt_id, body)

    async def remove_contact(self, cnt_id: int):
        return await self.repository.remove_contact(cnt_id)

    async def get_contacts_upcoming_birthdays(self, days: int, limit: int, offset: int):
        return await self.repository.get_contacts_upcoming_birthdays(
            days, limit, offset
        )
