import logging
from asyncio import wait_for
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db
from src.database.redis import get_redis_client

router = APIRouter(tags=["internal"])
logger = logging.getLogger("uvicorn.error")


@router.get("/health")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """K8s standart helth checker endpoint"""
    try:
        # Test the SQL DataBase connection
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database is not configured correctly",
        )

    try:
        # Test the Redis DB connection
        redis_client = get_redis_client()
        await wait_for(redis_client.ping(), timeout=2)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something is wrong with Redis",
        )

    return {"status": 1, "message": "App works!"}


@router.get("/")
@router.get("/about")
async def intro(request: Request):
    app = request.app
    return {"message": f"Wellcome to {app.title} v{app.version}"}
