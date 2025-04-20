import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UsersRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the UsersRepository with a database session.

        Args:
            session (AsyncSession): The SQLAlchemy asynchronous session for database operations.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by its ID from the database.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user with the given ID, or None if not found.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by its username from the database.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user with the given username, or None if not found.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by its email address from the database.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user with the given email address, or None if not found.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, body: UserCreate, hashed_password: str, avatar: str = None
    ) -> User:
        """
        Create a new user in the database.

        Args:
            body (UserCreate): The data for the user to create.
            hashed_password (str): The hashed password for the new user.
            avatar (str, optional): The avatar URL for the new user. Defaults to None.

        Returns:
            User: The newly created user.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            password=hashed_password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_password(self, user_id: id, hashed_password: str) -> User:
        """
        Reset the password associated with the given user ID.

        Args:
            user_id (int): The ID of the user to reset the password for.
            hashed_password (str): The hashed password to set for the user.

        Returns:
            User: The user with the updated password.
        """
        user = await self.get_user_by_id(user_id)
        user.password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirm the email address associated with the given email address.

        Args:
            email (str): The email address to confirm.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.email_confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the avatar URL for the user with the given email address.

        Args:
            email (str): The email address of the user whose avatar URL is to be updated.
            url (str): The new avatar URL to set for the user.

        Returns:
            User: The user with the updated avatar URL.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
