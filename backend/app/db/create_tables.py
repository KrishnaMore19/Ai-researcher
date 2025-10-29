import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.core.config import settings

# ✅ Import all models here so SQLAlchemy knows about them
from app.models import user, analytics, document, subscription

async def create_tables():
    """Creates all database tables asynchronously."""
    print("🚀 Connecting to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("📦 Creating all tables...")
        await conn.run_sync(Base.metadata.drop_all)   # Optional: drop all existing tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")

    await engine.dispose()
    print("🔌 Connection closed.")

if __name__ == "__main__":
    asyncio.run(create_tables())
