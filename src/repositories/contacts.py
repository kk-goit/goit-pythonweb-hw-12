import logging

from datetime import date, timedelta

from typing import Sequence
from pydantic import EmailStr

from sqlalchemy import select, union_all, or_, and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts import ContactsSchema, ContactsUpdateSchema

logger = logging.getLogger("uvicorn.error")


class ContactsRepository:
    def __init__(self, session: AsyncSession, user: User):
        self.db = session
        self.user = user

    async def get_contacts(
        self,
        limit: int,
        offset: int,
        first_name: str = None,
        last_name: str = None,
        email: EmailStr = None,
    ) -> Sequence[Contact]:
        stmt = select(Contact).filter_by(user_id=self.user.id)
        if first_name:
            stmt = stmt.filter(func.lower(Contact.first_name) == func.lower(first_name))
        if last_name:
            stmt = stmt.filter(func.lower(Contact.last_name) == func.lower(last_name))
        if email:
            stmt = stmt.filter(Contact.email == email)
        stmt = stmt.offset(offset).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, cnt_id: int) -> Contact | None:
        stmt = select(Contact).filter_by(user_id=self.user.id).filter_by(id=cnt_id)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactsSchema) -> Contact:
        contact = Contact(**body.model_dump(), user=self.user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, cnt_id: int) -> Contact | None:
        contact = await self.get_contact_by_id(cnt_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, cnt_id: int, body: ContactsUpdateSchema
    ) -> Contact | None:
        contact = await self.get_contact_by_id(cnt_id)
        if contact:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    def _get_upcoming_birthday_stmt(self, start_date: date, end_date: date):
        """Add filter of the birthdays for statement"""
        return (
            select(Contact)
            .filter_by(user_id=self.user.id)
            .filter(
                or_(
                    and_(
                        func.extract("month", Contact.birth_date)
                        == func.extract("month", start_date),
                        func.extract("day", Contact.birth_date)
                        >= func.extract("day", start_date),
                    ),
                    func.extract("month", Contact.birth_date)
                    > func.extract("month", start_date),
                )
            )
            .filter(
                or_(
                    func.extract("month", Contact.birth_date)
                    < func.extract("month", end_date),
                    and_(
                        func.extract("month", Contact.birth_date)
                        == func.extract("month", end_date),
                        func.extract("day", Contact.birth_date)
                        <= func.extract("day", end_date),
                    ),
                )
            )
            .order_by(
                func.extract("month", Contact.birth_date),
                func.extract("day", Contact.birth_date),
            )
        )

    async def get_contacts_upcoming_birthdays(self, days: int, limit: int, offset: int):
        today = date.today()
        end_date = today + timedelta(days=days)
        year_end = date(today.year, 12, 31)
        next_year = date(today.year + 1, 1, 1)

        logger.debug(
            f"Search contacts with birthdays for {days} days from {today} to {end_date}"
        )

        if end_date > year_end:
            stmt_current_year = self._get_upcoming_birthday_stmt(today, year_end)
            stmt_next_year = self._get_upcoming_birthday_stmt(next_year, end_date)
            stmt = select(
                aliased(
                    Contact, union_all(stmt_current_year, stmt_next_year).subquery()
                )
            )
        else:
            stmt = self._get_upcoming_birthday_stmt(today, end_date)

        contacts = await self.db.execute(stmt.limit(limit).offset(offset))
        return contacts.scalars().all()
