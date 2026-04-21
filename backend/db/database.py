from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import logging
from config import settings

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(settings.database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def create_tables() -> None:
    from sqlmodel import SQLModel
    from models.auth import User, Conversation, ChatMessage, MCPServer

    async with engine.begin() as conn:
        try:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")