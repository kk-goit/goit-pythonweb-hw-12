import redis.asyncio as redis
from src.conf.config import settings


def get_redis_client():
    return redis.from_url(settings.REDIS_URL)
