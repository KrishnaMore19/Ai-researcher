import asyncio
from app.db.base import Base
from app.db.session import engine

# Import all models to register them with Base
from app.models import user, document, chat, note, analytics, subscription

async def init_db():
    """Initialize the database: create all tables."""
    async with engine.begin() as conn:
        # Uncomment to drop all tables first (BE CAREFUL!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully!")
    print(f"✅ Created tables: {list(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    asyncio.run(init_db())