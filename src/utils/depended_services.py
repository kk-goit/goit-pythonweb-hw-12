from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, UserRole
from src.services.auth import AuthService, oauth2_scheme
from src.services.users import UsersService


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)


def get_users_service(db: AsyncSession = Depends(get_db)):
    return UsersService(db)


async def get_authorized_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)


def get_admin_user(current_user: User = Depends(get_authorized_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient access rights")
    return current_user
