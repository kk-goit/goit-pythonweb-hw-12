import logging
import json
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.conf.config import settings
from src.database.redis import get_redis_client
from src.entity.models import User, UserRole
from src.repositories.users import UsersRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")

redis_client = get_redis_client()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UsersRepository(self.db)

    def _hash_password(self, password: str) -> str:  # noqa
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str):  # noqa
        return hashlib.sha256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not confirmed yet",
            )

        if not self._verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        await self._store_user_to_cache(user)

        return user

    async def register_user(self, user_data: UserCreate) -> User:
        if await self.user_repository.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )
        if await self.user_repository.get_user_by_email(str(user_data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )

        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            logger.error(e)

        hashed_password = self._hash_password(user_data.password)
        user = await self.user_repository.create_user(
            user_data, hashed_password, avatar
        )
        return user

    def create_access_token(self, user_id: int) -> str:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {"sub": f"{user_id}", "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def revoke_access_token(self, token: str) -> None:
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        logger.debug(
            "Revoked auth token %s", exp - datetime.now(timezone.utc).timestamp()
        )
        if exp:
            await redis_client.setex(
                f"bl:{token}", int(exp - datetime.now(timezone.utc).timestamp()), "1"
            )

        await self._clear_user_from_cache(int(payload.get("sub")))
        return None

    def decode_and_validate_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token wrong"
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        if await redis_client.exists(f"bl:{token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked"
            )

        payload = self.decode_and_validate_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None or not user_id.isdigit():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        user = await self._get_cached_user_by_id(int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        return user

    async def _get_cached_user_by_id(self, user_id: int) -> User:
        user_data = await redis_client.get(f"usr:{user_id}")
        if user_data is None:
            user = await self.user_repository.get_user_by_id(int(user_id))
            if not user is None:
                await self._store_user_to_cache(user)
        else:
            logger.debug("Read cached user %s from REDIS", user_id)
            user = User(**json.loads(user_data))

        return user

    async def _store_user_to_cache(self, user: User) -> None:
        logger.debug("Cached user id:%s", user.id)
        await redis_client.setex(
            f"usr:{user.id}", settings.CACHE_TTL_SEC, user.to_jsons()
        )

    async def _clear_user_from_cache(self, user_id: int) -> None:
        logger.debug("Delete user id:%s from REDIS cache", user_id)
        await redis_client.delete(f"usr:{user_id}")
