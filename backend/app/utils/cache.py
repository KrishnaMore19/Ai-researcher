# app/utils/cache.py
"""
cache.py – Centralized caching utility using Redis.
Used for storing embeddings, chat context, summaries, and session data.
"""

import json
import asyncio
from typing import Optional, Any
import redis.asyncio as redis
from loguru import logger
from app.core.config import settings


# ---------------------------------
# 🔧 Initialize Redis Connection
# ---------------------------------
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """
    Initialize Redis client (called on startup).
    """
    global redis_client
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")


# ---------------------------------
# 💾 Cache Operations
# ---------------------------------

async def set_cache(key: str, value: Any, expire_seconds: int = 3600):
    """
    Store data in Redis cache (default expiry: 1 hour).
    Automatically converts objects to JSON.
    """
    if not redis_client:
        await init_redis()

    try:
        serialized = json.dumps(value)
        await redis_client.set(key, serialized, ex=expire_seconds)
    except Exception as e:
        logger.error(f"❌ Error setting cache: {e}")


async def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve cached data from Redis by key.
    Automatically converts JSON back to Python.
    """
    if not redis_client:
        await init_redis()

    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"❌ Error getting cache: {e}")
        return None


async def delete_cache(key: str):
    """
    Delete specific cache key.
    """
    if not redis_client:
        await init_redis()

    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.error(f"❌ Error deleting cache: {e}")


async def clear_cache():
    """
    Clear **all** keys in Redis (⚠️ use carefully in production).
    """
    if not redis_client:
        await init_redis()

    try:
        await redis_client.flushall()
        logger.warning("⚠️ Redis cache cleared.")
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")