from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from .database import AuthDatabase
from .dependencies import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_auth_database,
    generate_refresh_token,
    store_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
)
from .models import (
    UserLogin,
    Token,
    TokenWithRefresh,
    RefreshTokenRequest,
    UserResponse,
    UserModel,
    UserCreate,
)
from ...config import get_config

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
async def register(
    user_create: UserCreate, auth_db: AuthDatabase = Depends(get_auth_database)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = await auth_db.get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    try:
        # Create new user
        new_user = await auth_db.create_user(user_create)
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            username=new_user.username,
            email_verified=new_user.email_verified,
            status=new_user.status,
            avatar_url=new_user.avatar_url,
            preferred_language=new_user.preferred_language,
            timezone=new_user.timezone,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.post("/login", response_model=TokenWithRefresh)
async def login(
    user_login: UserLogin, auth_db: AuthDatabase = Depends(get_auth_database)
):
    """Login endpoint to authenticate user and return JWT token with refresh token"""
    app_config = get_config()

    user = await authenticate_user(user_login.email, user_login.password, auth_db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=app_config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    # Generate and store refresh token
    refresh_token = generate_refresh_token()
    await store_refresh_token(
        user_id=user.id,
        refresh_token=refresh_token,
        auth_db=auth_db,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_db: AuthDatabase = Depends(get_auth_database),
):
    """Refresh access token using refresh token"""
    app_config = get_config()

    # Validate refresh token
    user = await validate_refresh_token(refresh_request.refresh_token, auth_db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new access token
    access_token_expires = timedelta(minutes=app_config.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    refresh_request: RefreshTokenRequest,
    auth_db: AuthDatabase = Depends(get_auth_database),
):
    """Logout by revoking refresh token"""
    try:
        await revoke_refresh_token(refresh_request.refresh_token, auth_db)
        return {"detail": "Successfully logged out"}
    except Exception:
        # Even if revocation fails, we return success to avoid information leakage
        return {"detail": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: UserModel = Depends(get_current_user),
    auth_db: AuthDatabase = Depends(get_auth_database),
):
    """Logout from all devices by revoking all refresh tokens"""
    await revoke_all_refresh_tokens(current_user.id, auth_db)
    return {"detail": "Successfully logged out from all devices"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        email_verified=current_user.email_verified,
        status=current_user.status,
        avatar_url=current_user.avatar_url,
        preferred_language=current_user.preferred_language,
        timezone=current_user.timezone,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
