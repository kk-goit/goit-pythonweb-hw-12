from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf.config import settings


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.EMAIL_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect email confirmation token",
        )
