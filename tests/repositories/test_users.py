import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.users import UsersRepository
from src.entity.models import User
from src.schemas.user import UserCreate

@pytest.fixture
def users_repository():
    db = AsyncMock(spec=AsyncSession)
    return UsersRepository(db)

@pytest.fixture
def user():
    return User(id=1, username="test_user", email="test@example.com")

@pytest.mark.asyncio
async def test_get_user_by_id_exists(users_repository, user):
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = user
    users_repository.db.execute.return_value = execute_result
    result = await users_repository.get_user_by_id(1)
    assert result == user

@pytest.mark.asyncio
async def test_get_user_by_id_not_exists(users_repository):
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    users_repository.db.execute.return_value = execute_result
    result = await users_repository.get_user_by_id(1)
    assert result is None

@pytest.mark.asyncio
async def test_get_user_by_username_exists(users_repository, user):
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = user
    users_repository.db.execute.return_value = execute_result

    result = await users_repository.get_user_by_username(user.username)

    # Assert
    assert result == user

@pytest.mark.asyncio
async def test_get_user_by_username_not_exists(users_repository):
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    users_repository.db.execute.return_value = execute_result

    result = await users_repository.get_user_by_username("nonexistent_username")

    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_user_by_email_valid_email(users_repository, user):
    email = "test@example.com"
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = user
    users_repository.db.execute.return_value = execute_result
    
    result = await users_repository.get_user_by_email(email)

    # Assert
    assert result == user

@pytest.mark.asyncio
async def test_get_user_by_email_invalid_email(users_repository, user):
    email = "invalid_email"
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    users_repository.db.execute.return_value = execute_result
    
    result = await users_repository.get_user_by_email(email)

    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_user_by_email_email_not_in_database(users_repository, user):
    email = "test@example.com"
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    users_repository.db.execute.return_value = execute_result
    
    result = await users_repository.get_user_by_email(email)

    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_create_user_success(users_repository, user):
    users_repository.db.add = MagicMock()
    users_repository.db.commit = AsyncMock()
    users_repository.db.refresh = AsyncMock()

    body = UserCreate(
        username="test_user",
        email="test@example.com",
        password="plain_password"
    )

    result = await users_repository.create_user(body, "hashed_password")

    # Assert
    assert result.username == user.username
    assert result.email == user.email
    assert result.password == "hashed_password"

    users_repository.db.add.assert_called_once_with(result)
    users_repository.db.commit.assert_called_once()
    users_repository.db.refresh.assert_called_once_with(result)

@pytest.mark.asyncio
async def test_create_user_commit_failure(users_repository, user):
    users_repository.db.add = MagicMock()
    users_repository.db.commit = AsyncMock(side_effect=Exception("Database error"))
    users_repository.db.refresh = AsyncMock()

    body = UserCreate(
        username="test_user",
        email="test@example.com",
        password="plain_password"
    )

    # Assert
    with pytest.raises(Exception, match="Database error"):
        await users_repository.create_user(body, "hashed_password")

    users_repository.db.add.assert_called_once()
    users_repository.db.commit.assert_called_once()
    users_repository.db.refresh.assert_not_called()

@pytest.mark.asyncio
async def test_reset_password_success(users_repository, user):
    users_repository.db.commit = AsyncMock()
    users_repository.db.refresh = AsyncMock()
    users_repository.get_user_by_id = AsyncMock(return_value=user)
    new_password = "new_hashed_password"

    result = await users_repository.reset_password(user.id, new_password)

    # Assert
    assert result == user
    assert user.password == new_password
    users_repository.db.commit.assert_called_once()
    users_repository.db.refresh.assert_called_once_with(user)

@pytest.mark.asyncio
async def test_reset_password_commit_failure(users_repository, user):
    users_repository.db.commit = AsyncMock(side_effect=Exception("Database error"))
    users_repository.db.refresh = AsyncMock()
    users_repository.get_user_by_id = AsyncMock(return_value=user)

    new_password = "new_hashed_password"

    # Assert
    with pytest.raises(Exception, match="Database error"):
        await users_repository.reset_password(user.id, new_password)

    assert user.password == new_password 
    users_repository.db.commit.assert_called_once()
    users_repository.db.refresh.assert_not_called()
    users_repository.get_user_by_id.assert_called_once_with(user.id)

@pytest.mark.asyncio
async def test_confirmed_email_success(users_repository, user):
    users_repository.db.commit = AsyncMock()
    users_repository.get_user_by_email = AsyncMock(return_value=user)

    await users_repository.confirmed_email(user.email)

    # Assert
    assert user.email_confirmed
    users_repository.db.commit.assert_called_once()
    users_repository.get_user_by_email.assert_called_once_with(user.email)

@pytest.mark.asyncio
async def test_update_avatar_url_success(users_repository, user):
    users_repository.db.commit = AsyncMock()
    users_repository.db.refresh = AsyncMock()
    users_repository.get_user_by_email = AsyncMock(return_value=user)
    avatar_url = "new_avatar_url"

    result = await users_repository.update_avatar_url(user.email, avatar_url)

    # Assert
    assert result == user
    assert result.avatar == avatar_url
    users_repository.db.commit.assert_called_once()
    users_repository.db.refresh.assert_called_once_with(user)
    users_repository.get_user_by_email.assert_called_once_with(user.email)