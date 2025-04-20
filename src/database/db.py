import contextlib
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Initialize the DatabaseSessionManager.

        Args:
            url (str): The SQLAlchemy database URL.

        Attributes:
            _engine (AsyncEngine | None): The SQLAlchemy engine.
            _session_maker (async_sessionmaker): The session maker.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Create a database session as an asynchronous context manager.

        This method is meant to be used with the `async with` statement.

        It will create a new database session, commit it on success, and rollback
        on failure. If an exception occurs, it will be logged and re-raised.

        If the session manager has not been initialized, it will raise an
        Exception.

        Yields:
            Session: The database session.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Dependency for accessing the database session.

    This asynchronous generator function provides a database session
    for use in route handlers or other parts of the application. It yields
    a session object, which can be used to interact with the database.

    The session is automatically closed after use, and in the event of an
    exception, the session is rolled back. This function should be used
    with FastAPI's `Depends` to inject the session into request handlers.

    Yields:
        AsyncSession: The database session.
    """

    logger.debug(f"DB_URL: {settings.DB_URL}")
    async with sessionmanager.session() as session:
        yield session
