from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, UserRole
from src.services.auth import AuthService, oauth2_scheme
from src.services.users import UsersService


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency for accessing the authentication service.

    This function returns an instance of the AuthService class, which provides methods
    for authentication and authorization.

    The instance is created with a database session, which is obtained using the
    get_db dependency.

    Args:
        db (AsyncSession): The database session.

    Returns:
        AuthService: The instance of AuthService.
    """
    return AuthService(db)


def get_users_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency for accessing the users service.

    This function returns an instance of the UsersService class, which provides methods
    for user-related operations.

    The instance is created with a database session, which is obtained using the
    get_db dependency.

    Args:
        db (AsyncSession): The database session.

    Returns:
        UsersService: The instance of UsersService.
    """
    return UsersService(db)


async def get_authorized_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Dependency for accessing the currently authenticated user.

    This function returns the currently authenticated user, based on the given access token.

    The user is retrieved from the database using the authentication service.

    Args:
        token (str): The access token to use for authentication.
        auth_service (AuthService): The authentication service, obtained via dependency injection.

    Returns:
        User: The currently authenticated user.

    Raises:
        HTTPException: If the access token is invalid or the user is not authenticated.
    """
    return await auth_service.get_current_user(token)


def get_admin_user(current_user: User = Depends(get_authorized_user)):
    """
    Dependency for accessing the currently authenticated user with admin rights.

    This function returns the currently authenticated user if they have admin rights.
    Otherwise, it raises an HTTPException with a 403 status code.

    Args:
        current_user (User): The currently authenticated user, obtained via dependency injection.

    Returns:
        User: The currently authenticated user with admin rights.

    Raises:
        HTTPException: If the user does not have admin rights.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient access rights")
    return current_user
