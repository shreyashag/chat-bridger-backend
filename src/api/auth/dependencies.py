from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Tuple
import hashlib
import secrets
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .database import AuthDatabase, SupabaseAuthDatabase
from .models import UserModel
from ...config import get_config

# Security scheme
security = HTTPBearer()

# Token cache with expiration tracking
# Format: {token: (user_id, expiration_timestamp)}
_token_cache: Dict[str, Tuple[Optional[str], float]] = {}


def get_auth_database() -> AuthDatabase:
    """Get auth database instance (cached)"""
    app_config = get_config()

    supabase_url = app_config.auth_supabase_url
    supabase_key = app_config.auth_supabase_key

    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
        )

    return SupabaseAuthDatabase(supabase_url, supabase_key)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    app_config = get_config()

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=app_config.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, app_config.jwt_secret_key, algorithm=app_config.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user ID"""
    app_config = get_config()

    try:
        payload = jwt.decode(
            token, app_config.jwt_secret_key, algorithms=[app_config.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.PyJWTError:
        return None


def _cached_verify_token(token: str) -> Optional[str]:
    """Cached version of token verification with expiration awareness"""
    current_time = time.time()
    
    # Check if token is in cache and not expired
    if token in _token_cache:
        user_id, exp_timestamp = _token_cache[token]
        if current_time < exp_timestamp:
            return user_id
        else:
            # Token expired, remove from cache
            del _token_cache[token]
    
    # Verify token and cache result with expiration
    app_config = get_config()
    try:
        payload = jwt.decode(
            token, app_config.jwt_secret_key, algorithms=[app_config.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        exp: int = payload.get("exp", 0)
        
        if user_id and exp > current_time:
            # Cache the token with its expiration time
            _token_cache[token] = (user_id, float(exp))
            
            # Clean up old entries if cache gets too large
            if len(_token_cache) > 1000:
                # Remove expired entries
                expired_tokens = [k for k, (_, exp) in _token_cache.items() if exp <= current_time]
                for k in expired_tokens:
                    del _token_cache[k]
            
            return user_id
    except jwt.PyJWTError:
        pass
    
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_db: AuthDatabase = Depends(get_auth_database),
) -> UserModel:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = _cached_verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    user = await auth_db.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token (optimized for frequent calls)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = _cached_verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    return user_id


async def authenticate_user(
    email: str, password: str, auth_db: AuthDatabase
) -> Optional[UserModel]:
    """Authenticate user with email and password"""
    user = await auth_db.get_user_by_email(email)
    if not user:
        return None

    if not await auth_db.verify_password(password, user.password_hash):
        return None

    return user


def generate_refresh_token() -> str:
    """Generate a secure refresh token"""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(
    user_id: str,
    refresh_token: str,
    auth_db: AuthDatabase,
    expires_delta: Optional[timedelta] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Store refresh token in database"""
    if expires_delta is None:
        expires_delta = timedelta(days=30)  # Default 30 days for refresh tokens
    
    token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.utcnow() + expires_delta
    
    await auth_db.store_refresh_token(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at.isoformat(),
        user_agent=user_agent,
        ip_address=ip_address,
    )


async def validate_refresh_token(
    refresh_token: str,
    auth_db: AuthDatabase,
) -> Optional[UserModel]:
    """Validate refresh token and return associated user"""
    token_hash = hash_refresh_token(refresh_token)
    
    # Get token from database
    token_data = await auth_db.get_refresh_token(token_hash)
    if not token_data:
        return None
    
    # Update last_used_at
    await auth_db.update_refresh_token_usage(
        token_data["id"], 
        datetime.utcnow().isoformat()
    )
    
    # Get user
    user = await auth_db.get_user_by_id(token_data["user_id"])
    return user


async def revoke_refresh_token(
    refresh_token: str,
    auth_db: AuthDatabase,
) -> None:
    """Revoke a refresh token"""
    token_hash = hash_refresh_token(refresh_token)
    await auth_db.delete_refresh_token(token_hash)


async def revoke_all_refresh_tokens(
    user_id: str,
    auth_db: AuthDatabase,
) -> None:
    """Revoke all refresh tokens for a user"""
    await auth_db.delete_user_refresh_tokens(user_id)
