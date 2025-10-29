# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # -------------------------
    # App Configuration
    # -------------------------
    APP_NAME: str
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # -------------------------
    # Auth / Security
    # -------------------------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PASSWORD_HASH_SCHEME: str = "bcrypt"
    OAUTH2_TOKEN_URL: str = "/api/v1/auth/login"

    # -------------------------
    # Database
    # -------------------------
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DOCKER: bool = False
    DATABASE_URL: str

    # -------------------------
    # Vector DB
    # -------------------------
    CHROMA_DB_DIR: str
    CHROMA_COLLECTION: str

    # -------------------------
    # Redis
    # -------------------------
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # -------------------------
    # Logging
    # -------------------------
    LOG_LEVEL: str
    LOG_FILE: str
    ERROR_LOG_FILE: str
    ACCESS_LOG_FILE: str

    # -------------------------
    # Storage
    # -------------------------
    UPLOAD_DIR: str
    PROCESSED_DIR: str
    TEMP_DIR: str

    # -------------------------
    # AI Models
    # -------------------------
    LLAMA_MODEL: str
    LLAMA_API_KEY: str
    DOLPHIN_MODEL: str
    DOLPHIN_API_KEY: str
    GEMMA_MODEL: str
    GEMMA_API_KEY: str

    EMBEDDING_MODEL: str
    EMBEDDING_DIM: int
    MAX_TOKENS: int
    TEMPERATURE: float

    # -------------------------
    # LangChain / Agents
    # -------------------------
    LANGCHAIN_VERBOSE: bool = True
    LANGCHAIN_TRACING_V2: bool = False
    AGENT_MODE: str = "researcher"

    # -------------------------
    # Email (Optional)
    # -------------------------
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    # -------------------------
    # Payment Gateway (Razorpay)
    # -------------------------
    PAYMENT_PROVIDER: str = "razorpay"
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    PAYMENT_SUCCESS_URL: str = "http://localhost:3000/success"
    PAYMENT_CANCEL_URL: str = "http://localhost:3000/cancel"
    CURRENCY: str = "INR"

    # -------------------------
    # Validators
    # -------------------------
    @field_validator("CORS_ORIGINS", mode="before")
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.replace("[", "").replace("]", "").replace('"', "").split(",")]
        return v

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v, info):
        """
        Build DATABASE_URL from individual components if not provided directly
        """
        if isinstance(v, str) and v:
            return v
        
        # Access other fields from info.data
        data = info.data
        user = data.get("DATABASE_USER")
        password = data.get("DATABASE_PASSWORD")
        host = data.get("DATABASE_HOST")
        port = data.get("DATABASE_PORT")
        db = data.get("DATABASE_NAME")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()