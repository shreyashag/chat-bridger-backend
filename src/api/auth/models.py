from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User creation model"""

    email: EmailStr
    password: str
    username: Optional[str] = None
    email_verified: bool = False
    status: str = "active"
    avatar_url: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"


class UserLogin(BaseModel):
    """User login model"""

    email: EmailStr = Field(
        description="User's email address", examples=["test@example.com"]
    )
    password: str = Field(description="User's password", examples=["password123"])


class UserModel(BaseModel):
    """User model"""

    id: str
    email: str
    password_hash: str
    username: Optional[str] = None
    email_verified: bool = False
    status: str = "active"  # active, suspended, pending_verification
    avatar_url: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    """User response model (without password hash)"""

    id: str
    email: str
    username: Optional[str] = None
    email_verified: bool = False
    status: str = "active"
    avatar_url: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str = "bearer"


class TokenWithRefresh(Token):
    """Token response model with refresh token"""

    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""

    refresh_token: str
