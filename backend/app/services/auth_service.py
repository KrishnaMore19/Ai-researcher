# app/services/auth_service.py

from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import UserCreate, UserRead, TokenResponse
from app.db.session import get_db
from app.core.config import settings

# ----------------------
# Password Hashing Setup
# ----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------------
# OAuth2 Scheme
# ----------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.OAUTH2_TOKEN_URL)

# ----------------------
# Utility Functions
# ----------------------
def safe_bcrypt_password(password: str) -> str:
    """
    Truncate password safely to 72 bytes for bcrypt.
    Handles multi-byte UTF-8 characters.
    """
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        encoded = encoded[:72]
        password = encoded.decode("utf-8", errors="ignore")
    return password

def hash_password(password: str) -> str:
    truncated = safe_bcrypt_password(password)
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = safe_bcrypt_password(plain_password)
    return pwd_context.verify(truncated, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode a JWT token and return the payload"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ----------------------
# AuthService Class
# ----------------------
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> UserRead:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user with safe password
        new_user = User(
            id=str(uuid.uuid4()),
            full_name=user_data.full_name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            is_active=True,
            is_superuser=False
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return UserRead(
            id=new_user.id,
            full_name=new_user.full_name,
            email=new_user.email,
            is_active=new_user.is_active,
            is_superuser=new_user.is_superuser,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )

    async def authenticate_user(self, email: str, password: str) -> Optional[TokenResponse]:
        """Validate user credentials and return token"""
        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get the current logged-in user from JWT token"""
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user

    @staticmethod
    async def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Ensure the user is active"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user

    @staticmethod
    async def refresh_token(current_user: User) -> TokenResponse:
        """Generate a new token for the current user"""
        access_token = create_access_token(
            data={"sub": current_user.email, "user_id": str(current_user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )