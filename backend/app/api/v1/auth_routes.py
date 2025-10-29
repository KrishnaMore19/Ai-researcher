# app/api/v1/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import user as user_schema
from app.services.auth_service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/auth")

# ------------------------------
# Login (OAuth2 form)
# ------------------------------
@router.post("/login", response_model=user_schema.TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    # OAuth2PasswordRequestForm uses 'username' field for email
    token = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return token

# ------------------------------
# Register / Signup
# ------------------------------
@router.post("/register", response_model=user_schema.UserResponse)
async def register(
    data: user_schema.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.create_user(data)
    return user

# ------------------------------
# Refresh Token
# ------------------------------
@router.post("/refresh", response_model=user_schema.TokenResponse)
async def refresh_token(current_user=Depends(AuthService.get_current_user)):
    token = await AuthService.refresh_token(current_user)
    return token
