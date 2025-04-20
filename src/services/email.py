import logging
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.utils.email_tokens import create_email_token

logger = logging.getLogger("uvicorn.error")

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(
    email: EmailStr,
    username: str,
    host: str,
    subject: str,
    template_name: str,
    exp_days: int,
) -> None:
    """
    Send an email to the user with a token to be used to confirm email or restore password.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        host (str): The host of the API.
        subject (str): The subject of the email.
        template_name (str): The name of the template to be used.
        exp_days (int): The number of days the token will be valid.

    Returns:
        None
    """
    try:
        token_verification = create_email_token({"sub": email}, exp_days)
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
    except ConnectionErrors as err:
        logger.error(err)


async def send_pwd_restore_email(email: EmailStr, username: str, host: str) -> None:
    """
    Send an email to the user with a password reset token.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        host (str): The host of the API.

    Returns:
        None
    """
    return await send_email(
        email,
        username,
        host,
        "Reset password for API",
        "pwd_restore_email.html",
        settings.EMAIL_PASSWORD_TOKEN_EXPIRE_DAYS,
    )


async def send_confirmation_email(email: EmailStr, username: str, host: str) -> None:
    """
    Send an email to the user with a confirmation token.

    Args:
        email (EmailStr): The email address of the user.
        username (str): The username of the user.
        host (str): The host of the API.

    Returns:
        None
    """

    return await send_email(
        email,
        username,
        host,
        "Confirm your email",
        "confirm_email.html",
        settings.EMAIL_TOKEN_EXPIRE_DAYS,
    )
