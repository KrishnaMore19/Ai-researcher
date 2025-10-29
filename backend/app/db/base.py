# app/db/base.py
from sqlalchemy.orm import declarative_base

# Base class for all models
Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models import (
    user,
    document,
    note,
    chat,
    analytics,
    subscription,
    
)
