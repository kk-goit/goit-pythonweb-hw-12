import logging
import json
import secrets
import string
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.conf.config import settings
from src.conf.constants import PASSWD_MAX_LENGTH
from src.database.redis import get_redis_client, rewoke_jwt_token, is_jwt_token_rewoked
from src.entity.models import User, UserRole
from src.repositories.users import UsersRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")

redis_client = get_redis_client()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the AuthService with a database session.

        Args:
            db (AsyncSession): The SQLAlchemy asynchronous session for database operations.
        """
        self.db = db
        self.user_repository = UsersRepository(self.db)

    def _hash_password(self, password: str) -> str:  # noqa
        """
        Hash the given password using the bcrypt algorithm.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a given password against a hashed password using the bcrypt algorithm.

        Args:
            plain_password (str): The plain password to verify.
            hashed_password (str): The hashed password to verify against.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str):  # noqa
        """
        Hash the given token using the SHA-256 algorithm.

        Args:
            token (str): The token to hash.

        Returns:
            str: The hashed token as a hexadecimal string.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_password(self) -> str: #noqa
        """
        Generate a random password of maximum length.

        The generated password is a random sequence of ASCII letters, digits and
        the following special characters: "+-=_/".

        Returns:
            str: The generated password.
        """
        characters = string.ascii_letters + string.digits + "+-=_/"
        return ''.join(secrets.choice(characters) for _ in range(PASSWD_MAX_LENGTH))

    async def authenticate(self, username: str, password: str) -> User:
        """
        Authenticate a user by username and password.

        Args:
            username (str): The username to authenticate.
            password (str): The password to authenticate with.

        Returns:
            User: The authenticated user.

        Raises:
            HTTPException: If the username or password are incorrect,
                or if the user's email is not confirmed yet.
        """
        
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
        """
        Register a new user.

        Args:
            user_data (UserCreate): The user data to register.

        Returns:
            User: The newly created user.

        Raises:
            HTTPException: If a user with the given username or email already exists.
        """
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

    async def reset_password(self, user_id: int) -> dict:
        """
        Reset the password for a user and return the updated user information along with the new password.

        Args:
            user_id (int): The ID of the user whose password is to be reset.

        Returns:
            dict: A dictionary containing the updated user information and the new password.

        Raises:
            HTTPException: If the user with the given ID does not exist.
        """
        new_password = self._generate_password()
        hashed_password = self._hash_password(new_password)
        user = await self.user_repository.reset_password(user_id, hashed_password)
        return dict(user.to_dict(), new_password = new_password)

    def create_access_token(self, user_id: int) -> str:
        """
        Create an access token for the given user.

        Args:
            user_id (int): The ID of the user to create the token for.

        Returns:
            str: The access token for the given user.

        The access token is a JSON Web Token (JWT) signed with the secret key
        and containing the user's ID and the expiration timestamp.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {"sub": f"{user_id}", "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def revoke_access_token(self, token: str) -> None:
        """
        Revoke the given access token.

        Args:
            token (str): The access token to revoke.

        This function decodes and validates the given access token, then revokes it
        by setting a flag in Redis with the same value as the token. It also clears
        the user's cache entry so that the user's information will be reloaded from
        the database on the next request.

        If the token is invalid, it raises an HTTPException with a 401 status code.
        """
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        await rewoke_jwt_token(redis_client, token, exp)

        await self._clear_user_from_cache(int(payload.get("sub")))
        return None

    def decode_and_validate_access_token(self, token: str) -> dict:
        """
        Decodes and validates the given access token.

        Args:
            token (str): The access token to decode and validate.

        Returns:
            dict: The decoded payload of the access token.

        Raises:
            HTTPException: If the token is invalid, with a 401 status code.
        """
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
        """
        Returns the current user associated with the given access token.

        Args:
            token (str): The access token to use.

        Returns:
            User: The current user associated with the given access token.

        Raises:
            HTTPException: If the token is revoked, invalid or the user associated
                with it doesn't exist, with a 401 status code.
        """
        if await is_jwt_token_rewoked(redis_client, token):
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
        """
        Retrieve a user from the Redis cache by its ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The user with the given ID, or None if not found in the cache.

        Note:
            If the user is not found in the cache, it is retrieved from the
            database and stored in the cache for future requests.
        """
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
        """
        Store a user in the Redis cache.

        Args:
            user (User): The user object to store in the cache.

        Returns:
            None

        Note:
            The user data is serialized to JSON format and stored with an expiration
            time defined by the CACHE_TTL_SEC setting.
        """
        logger.debug("Cached user id:%s", user.id)
        await redis_client.setex(
            f"usr:{user.id}", settings.CACHE_TTL_SEC, user.to_jsons()
        )

    async def _clear_user_from_cache(self, user_id: int) -> None:
        """
        Clear the user with the given ID from the Redis cache.

        Args:
            user_id (int): The ID of the user to remove from the cache.

        Returns:
            None

        Note:
            This method is used to clear the user from the cache after a successful
            login or logout. This ensures that the user's data is reloaded from
            the database on the next request.
        """
        logger.debug("Delete user id:%s from REDIS cache", user_id)
        await redis_client.delete(f"usr:{user_id}")
