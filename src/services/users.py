from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.users import UsersRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UsersService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the UsersService with a database session.

        Args:
            db (AsyncSession): The SQLAlchemy asynchronous session for database operations.
        """
        self.db = db
        self.users_repository = UsersRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data (UserCreate): The data for the user to create.

        Returns:
            User: The newly created user.
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by its username from the database.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user with the given username, or None if not found.
        """
        user = await self.users_repository.get_user_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by its email address from the database.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user with the given email address, or None if not found.
        """
        user = await self.users_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirm the email address associated with the given email address.

        Args:
            email (str): The email address to confirm.

        Returns:
            None
        """
        user = await self.users_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        """
        Update the avatar URL for the user with the given email address.

        Args:
            email (str): The email address of the user whose avatar URL is to be updated.
            url (str): The new avatar URL to set for the user.

        Returns:
            User: The user with the updated avatar URL.
        """
        return await self.users_repository.update_avatar_url(email, url)
