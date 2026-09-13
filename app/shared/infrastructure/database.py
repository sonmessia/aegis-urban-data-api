"""Async SQLAlchemy 2.0 session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class DatabaseSessionManager:
    """
    Manages the async SQLAlchemy engine and session factory.
    Initialised once at startup via lifespan, closed at shutdown.
    """

    def __init__(self) -> None:
        self._engine = None
        self._sessionmaker = None

    def init(self, database_url: str, pool_size: int = 10, max_overflow: int = 20) -> None:
        """Create engine and session factory. Call once at startup."""
        self._engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # detect stale connections
            echo=False,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # avoid implicit I/O after commit
        )

    async def close(self) -> None:
        """Dispose engine — called at shutdown."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncConnection, None]:
        """Yield a raw connection (for migrations / DDL)."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager not initialised — call init() first")
        async with self._engine.begin() as conn:
            yield conn

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a session with automatic rollback on error."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager not initialised — call init() first")
        session: AsyncSession = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Singleton — shared across the application
sessionmanager = DatabaseSessionManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — inject an AsyncSession into route handlers / dependencies.
    """
    async with sessionmanager.session() as session:
        yield session
