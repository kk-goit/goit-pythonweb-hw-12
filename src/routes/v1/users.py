import logging
from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.conf.config import settings
from src.utils.depended_services import (
    get_users_service,
    get_authorized_user,
    get_admin_user,
)
from src.utils.email_tokens import get_email_from_token
from src.entity.models import User
from src.schemas.user import UserResponse
from src.schemas.email import RequestEmail
from src.services.auth import oauth2_scheme
from src.services.users import UsersService
from src.services.email import send_email
from src.services.upload_to_cloudinary import UploadFileService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger("uvicorn.error")


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.LIMIT4_USERS_ME)
async def me(
    request: Request,
    user: User = Depends(get_authorized_user),
):
    return user


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, users_service: UsersService = Depends(get_users_service)
):
    email = get_email_from_token(token)
    user = await users_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.email_confirmed:
        return {"message": "Yours Email has already been confirmed"}
    await users_service.confirmed_email(email)
    return {"message": "Yours Email confirmed"}


@router.post("/resend_email")
@limiter.limit(settings.LIMIT4_USERS_RESENT)
async def resend_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    users_service: UsersService = Depends(get_users_service),
):
    user = await users_service.get_user_by_email(str(body.email))
    if user:
        if user.email_confirmed:
            return {"message": "This Email has already been confirmed"}
        else:
            background_tasks.add_task(
                send_email, user.email, user.username, str(request.base_url)
            )
    else:
        logger.warning("Tried to send email to not exist %s", str(body.email))

    return {"message": "Please check your inbox to receive a confirmation email"}


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_admin_user),
    users_service: UsersService = Depends(get_users_service),
):
    avatar_url = UploadFileService().upload_file(file, user.username)

    user = await users_service.update_avatar_url(user.email, avatar_url)

    return user

