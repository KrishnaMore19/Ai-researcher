# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# -------------------------
# App Settings and DB
# -------------------------
from app.core.config import settings
from app.db.session import engine

# Import Base and all models to register them
from app.models import (
    Base,
    User,
    Document,
    ChatMessage,
    Note,
    Analytics,
    Subscription,
    Billing
)

# -------------------------
# API Routers
# -------------------------
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.document_routes import router as document_router
from app.api.v1.notes_routes import router as notes_router
from app.api.v1.chat_routes import router as chat_router
from app.api.v1.analytics_routes import router as analytics_router
from app.api.v1.settings_routes import router as settings_router

# -------------------------
# Redis
# -------------------------
from app.utils.cache import init_redis, redis_client


# -------------------------
# Lifespan Context Manager
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events using lifespan context manager.
    """
    print(f"🚀 Starting {settings.APP_NAME}...")

    # 1️⃣ Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables initialized")

    # 2️⃣ Initialize Redis connection
    await init_redis()
    print("✅ Redis initialized")

    yield  # Application runs here

    # -------------------------
    # Shutdown
    # -------------------------
    print("🛑 Shutting down application...")
    
    if redis_client:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
        print("✅ Redis connection closed")

    await engine.dispose()
    print("✅ Database connection closed")


# -------------------------
# FastAPI App Instance
# -------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered research copilot with multi-model LLM support, document analysis, and RAG capabilities",
    version="1.0.0",
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# -------------------------
# CORS Middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Include API Routers
# -------------------------
app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(document_router, prefix=settings.API_V1_STR, tags=["Documents"])
app.include_router(notes_router, prefix=settings.API_V1_STR, tags=["Notes"])
app.include_router(chat_router, prefix=settings.API_V1_STR, tags=["Chat"])
app.include_router(analytics_router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(settings_router, prefix=settings.API_V1_STR, tags=["Settings"])

# -------------------------
# Root Endpoint
# -------------------------
@app.get("/", tags=["Root"])
async def root():
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# -------------------------
# Health Check Endpoint
# -------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "database": "connected",
        "redis": redis_status,
        "environment": settings.APP_ENV
    }

# -------------------------
# API Info Endpoint
# -------------------------
@app.get("/api/info", tags=["Info"])
async def api_info():
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "api_prefix": settings.API_V1_STR,
        "available_models": ["llama", "dolphin", "gemma"],
        "features": [
            "Multi-model LLM support",
            "Document upload & analysis",
            "RAG (Retrieval Augmented Generation)",
            "Note-taking with AI assistance",
            "Analytics & usage tracking",
            "Subscription management"
        ],
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth",
            "documents": f"{settings.API_V1_STR}/documents",
            "notes": f"{settings.API_V1_STR}/notes",
            "chat": f"{settings.API_V1_STR}/chat",
            "analytics": f"{settings.API_V1_STR}/analytics",
            "settings": f"{settings.API_V1_STR}/settings"
        }
    }

# -------------------------
# Run Application
# -------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
