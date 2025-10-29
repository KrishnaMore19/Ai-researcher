from app.db.base import Base
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

# Use your async database URL from .env
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

async def reset_db():
    async with engine.begin() as conn:
        print("🚨 Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped!")

        print("🛠️ Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_db())
