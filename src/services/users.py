from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.users import UsersRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users_repository = UsersRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.users_repository.get_user_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        user = await self.users_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        user = await self.users_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        return await self.users_repository.update_avatar_url(email, url)
