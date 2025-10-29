# app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# -------------------------
# Async SQLAlchemy Engine
# -------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,          # Logs SQL queries, set False in production
    future=True
)

# -------------------------
# Async session factory
# -------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# -------------------------
# Base class for models
# -------------------------
Base = declarative_base()

# -------------------------
# Dependency for FastAPI
# -------------------------
async def get_db() -> AsyncSession:
    """
    Get a database session for FastAPI routes
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
