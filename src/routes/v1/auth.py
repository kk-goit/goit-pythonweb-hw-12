import logging

from typing import Optional
from pydantic import EmailStr

from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks,
    Request,
)
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.email import send_email
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse, UserCreate
from src.utils.depended_services import get_auth_service

router = APIRouter(prefix="/auth", tags=["authorization"])
logger = logging.getLogger("uvicorn.error")

@router.post("/sign-up", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(
        send_email, user_data.email, user_data.username, str(request.base_url)
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(user.id)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.revoke_access_token(token)
    return None
