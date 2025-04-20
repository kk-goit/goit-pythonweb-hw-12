import logging
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis
from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


def get_redis_client() -> redis.Redis:
    """
    Initializes and returns a Redis client instance.

    Returns:
        redis.Redis: An instance of Redis client connected to the configured Redis URL.
    """

    return redis.from_url(settings.REDIS_URL)


async def rewoke_jwt_token(client: redis.Redis, token: str, exp: int) -> None:
    """
    Revokes a JWT token in Redis so that it can't be used after the call.

    Args:
    - client (redis.Redis): Redis client.
    - token (str): JWT token to be revoked.
    - exp (int): Expiration time of the token in seconds.
    """
    logger.debug("Revoked token %s", exp - datetime.now(timezone.utc).timestamp())
    if exp:
        await client.setex(
            f"bl:{token}", int(exp - datetime.now(timezone.utc).timestamp()), "1"
        )


async def is_jwt_token_rewoked(client: redis.Redis, token: str) -> bool:
    """
    Checks if a JWT token is revoked in Redis.

    Args:
        client (redis.Redis): Redis client.
        token (str): JWT token to be checked.

    Returns:
        bool: True if the token is revoked in Redis, False otherwise.
    """

    return await client.exists(f"bl:{token}")
