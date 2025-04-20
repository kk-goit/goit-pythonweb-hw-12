from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf.config import settings
from src.database.redis import get_redis_client, rewoke_jwt_token, is_jwt_token_rewoked

redis_client = get_redis_client()


def create_email_token(data: dict, exp_days: int = settings.EMAIL_TOKEN_EXPIRE_DAYS):
    """
    Create an email token to be used in email confirmation and password reset flows.

    Args:
        data (dict): Data to be encoded in the token.
        exp_days (int): Number of days the token will be valid.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=exp_days)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


async def get_email_from_token(token: str, check_rewoked: bool = False):
    """
    Retrieves the email address associated with the given token.

    Args:
        token (str): The email token to be decoded.
        check_rewoked (bool): Whether to check if the token has been revoked in Redis. Defaults to False.

    Returns:
        str: The email address associated with the given token.

    Raises:
        HTTPException: If the token is invalid or revoked.
    """
    token_exeption = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Incorrect email token",
    )

    if check_rewoked and await is_jwt_token_rewoked(redis_client, token):
        raise token_exeption

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        if check_rewoked:
            await rewoke_jwt_token(redis_client, token, payload["exp"])
        return email
    except jwt.PyJWTError as e:
        raise token_exeption
