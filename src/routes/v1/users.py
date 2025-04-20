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
    get_auth_service,
    get_authorized_user,
    get_admin_user,
)
from src.utils.email_tokens import get_email_from_token
from src.entity.models import User
from src.schemas.user import UserResponse, UserNewPasswordResponse
from src.schemas.email import RequestEmail
from src.services.auth import oauth2_scheme, AuthService
from src.services.users import UsersService
from src.services.email import send_confirmation_email, send_pwd_restore_email
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
    """
    Get information about the current authorized user.

    Returns:
        UserResponse: a UserResponse object containing the user's data.
    """
    return user


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, users_service: UsersService = Depends(get_users_service)
):
    """
    Confirm the email address associated with the given token.

    Args:
        token (str): A token that was sent to the user's email address.

    Returns:
        dict: A dict containing a message indicating the result of the operation.

    Raises:
        HTTPException: If the token is invalid or the user associated with it doesn't
            exist.
    """
    email = await get_email_from_token(token)
    user = await users_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.email_confirmed:
        return {"message": "Yours Email has already been confirmed"}
    await users_service.confirmed_email(email)
    return {"message": "Yours Email confirmed"}


@router.get("/reset_password/{token}", response_model=UserNewPasswordResponse)
async def reset_password(
    token: str,
    users_service: UsersService = Depends(get_users_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Reset the password associated with the given token.

    Args:
        token (str): A token that was sent to the user's email address.

    Returns:
        UserNewPasswordResponse: A UserNewPasswordResponse object containing the
            user's new password.

    Raises:
        HTTPException: If the token is invalid or the user associated with it doesn't
            exist.
    """
    email = await get_email_from_token(token, True)
    user = await users_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if not user.email_confirmed:
        await users_service.confirmed_email(email)
    user = await auth_service.reset_password(user.id)
    return user


@router.post("/resend_email")
@limiter.limit(settings.LIMIT4_USERS_RESENT)
async def resend_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    users_service: UsersService = Depends(get_users_service),
):
    """
    Resend the confirmation email to the user associated with the given email address.

    Args:
        body (RequestEmail): The email address to resend the confirmation email to.

    Returns:
        dict: A dict containing a message indicating the result of the operation.

    Raises:
        HTTPException: If the email address is invalid or the user associated with it
            doesn't exist.
    """
    user = await users_service.get_user_by_email(str(body.email))
    if user:
        if user.email_confirmed:
            return {"message": "This Email has already been confirmed"}
        else:
            background_tasks.add_task(
                send_confirmation_email,
                user.email,
                user.username,
                str(request.base_url),
            )
    else:
        logger.warning("Tried to send email to not exist %s", str(body.email))

    return {"message": "Please check your inbox to receive a confirmation email"}


@router.post("/reset_password")
@limiter.limit(settings.LIMIT4_USERS_PASSWD)
async def request_reset_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    users_service: UsersService = Depends(get_users_service),
):
    """
    Request to reset the password for the user associated with the given email address.

    Args:
        body (RequestEmail): The email address to send the password reset email to.

    Returns:
        dict: A dict containing a message indicating the result of the operation.

    Raises:
        HTTPException: If the email address is invalid or the user associated with it
            doesn't exist.
    """
    user = await users_service.get_user_by_email(str(body.email))
    if user:
        if not user.email_confirmed:
            return {"message": "This Email has not been confirmed"}
        else:
            background_tasks.add_task(
                send_pwd_restore_email, user.email, user.username, str(request.base_url)
            )
    else:
        logger.warning("Tried to send email to not exist %s", str(body.email))

    return {
        "message": "Please check your inbox to receive a email with password reset instruction"
    }


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_admin_user),
    users_service: UsersService = Depends(get_users_service),
):
    """
    Update the avatar of the current authorized user.

    Args:
        file (UploadFile): The avatar image file to be uploaded.
        user (User): The current authorized user, retrieved via dependency injection.
        users_service (UsersService): The users service for user-related operations,
            retrieved via dependency injection.

    Returns:
        UserResponse: A UserResponse object containing the updated user data with the new avatar URL.

    Raises:
        HTTPException: If the user is not authorized or an error occurs during the update.
    """

    avatar_url = UploadFileService().upload_file(file, user.username)

    user = await users_service.update_avatar_url(user.email, avatar_url)

    return user
