# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create async engine with production-ready pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # True in dev for debug
    pool_size=10,  # Max active connections
    max_overflow=20,  # Extra connections if pool is exhausted
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Dependency for FastAPI routes
async def get_db():
    """
    Provide a database session to endpoints using FastAPI Depends.
    Ensures session is closed after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
