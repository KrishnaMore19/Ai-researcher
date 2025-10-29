# create_database.py (in your project root, not in app/)
import asyncio
import asyncpg
from app.core.config import settings

async def create_database():
    """
    Create the PostgreSQL database if it doesn't exist.
    This must run BEFORE init_db.py
    """
    # Parse connection details from DATABASE_URL
    # Connect to 'postgres' default database first
    conn = await asyncpg.connect(
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database='postgres'  # Connect to default database
    )
    
    try:
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.DATABASE_NAME
        )
        
        if result:
            print(f"Database '{settings.DATABASE_NAME}' already exists.")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE {settings.DATABASE_NAME}')
            print(f"Database '{settings.DATABASE_NAME}' created successfully!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_database())