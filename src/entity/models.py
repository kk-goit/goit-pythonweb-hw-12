from datetime import datetime, date
from enum import Enum
from json import dumps

from sqlalchemy import (
    func,
    event,
    ForeignKey,
    Index,
    String,
    DateTime,
    Date,
    BigInteger,
    Enum as SqlEnum,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

from src.conf import constants


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    REGULAR = "regular"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(
        String(constants.EMAIL_MAX_LENGTH), nullable=False, unique=True
    )
    email_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.REGULAR, nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(256), nullable=True)

    def to_jsons(self):
        return dumps({
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "email_confirmed": self.email_confirmed,
            "role": self.role,
            "avatar": self.avatar
        })        


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(constants.EMAIL_MAX_LENGTH), nullable=True
    )
    phone: Mapped[int] = mapped_column(BigInteger, nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(
        String(constants.DESCRIPTION_MAX_LENGTH), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")


Index("Contacts_birth_date_idx", Contact.birth_date)


@event.listens_for(Contact, "before_insert")
async def validate_contact(mapper, connection, target):
    """Validate that Phone or Email or both are seted"""
    if target.email is None and target.phone is None:
        raise ValueError("Phone or Email must be declared")
