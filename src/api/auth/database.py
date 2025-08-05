from abc import ABC, abstractmethod
from typing import Optional

import bcrypt
from supabase import acreate_client, AsyncClient

from src.logging_config import get_logger
from .models import UserModel, UserCreate

logger = get_logger(__name__)


class AuthDatabase(ABC):
    """Abstract interface for authentication database operations"""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def create_user(self, user: UserCreate) -> UserModel:
        """Create new user"""
        pass

    @abstractmethod
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        pass

    @abstractmethod
    async def store_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Store refresh token in database"""
        pass

    @abstractmethod
    async def get_refresh_token(self, token_hash: str) -> Optional[dict]:
        """Get refresh token by hash"""
        pass

    @abstractmethod
    async def update_refresh_token_usage(self, token_id: str, last_used_at: str) -> None:
        """Update refresh token last usage time"""
        pass

    @abstractmethod
    async def delete_refresh_token(self, token_hash: str) -> None:
        """Delete a refresh token"""
        pass

    @abstractmethod
    async def delete_user_refresh_tokens(self, user_id: str) -> None:
        """Delete all refresh tokens for a user"""
        pass


class SupabaseAuthDatabase(AuthDatabase):
    """Supabase implementation of authentication database"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.supabase: Optional[AsyncClient] = None

    async def _get_client(self) -> AsyncClient:
        """Get or create Supabase client"""
        if self.supabase is None:
            self.supabase = await acreate_client(self.supabase_url, self.supabase_key)
        return self.supabase

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        try:
            client = await self._get_client()
            result = (
                await client.table("users").select("*").eq("email", email).execute()
            )

            if result.data:
                user_data = result.data[0]
                return UserModel(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=user_data["password_hash"],
                    username=user_data.get("username"),
                    email_verified=user_data.get("email_verified", False),
                    status=user_data.get("status", "active"),
                    avatar_url=user_data.get("avatar_url"),
                    preferred_language=user_data.get("preferred_language", "en"),
                    timezone=user_data.get("timezone", "UTC"),
                    created_at=user_data["created_at"],
                    updated_at=user_data["updated_at"],
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}", exc_info=True)
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID"""
        try:
            client = await self._get_client()
            result = await client.table("users").select("*").eq("id", user_id).execute()

            if result.data:
                user_data = result.data[0]
                return UserModel(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=user_data["password_hash"],
                    username=user_data.get("username"),
                    email_verified=user_data.get("email_verified", False),
                    status=user_data.get("status", "active"),
                    avatar_url=user_data.get("avatar_url"),
                    preferred_language=user_data.get("preferred_language", "en"),
                    timezone=user_data.get("timezone", "UTC"),
                    created_at=user_data["created_at"],
                    updated_at=user_data["updated_at"],
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}", exc_info=True)
            return None

    async def create_user(self, user: UserCreate) -> UserModel:
        """Create new user"""
        try:
            client = await self._get_client()
            password_hash = self._hash_password(user.password)

            # Prepare user data with defaults for new fields
            user_data_to_insert = {
                "email": user.email,
                "password_hash": password_hash,
                "username": getattr(user, "username", None),
                "email_verified": getattr(user, "email_verified", False),
                "status": getattr(user, "status", "active"),
                "avatar_url": getattr(user, "avatar_url", None),
                "preferred_language": getattr(user, "preferred_language", "en"),
                "timezone": getattr(user, "timezone", "UTC"),
            }

            result = await client.table("users").insert(user_data_to_insert).execute()

            if result.data:
                user_data = result.data[0]
                return UserModel(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=user_data["password_hash"],
                    username=user_data.get("username"),
                    email_verified=user_data.get("email_verified", False),
                    status=user_data.get("status", "active"),
                    avatar_url=user_data.get("avatar_url"),
                    preferred_language=user_data.get("preferred_language", "en"),
                    timezone=user_data.get("timezone", "UTC"),
                    created_at=user_data["created_at"],
                    updated_at=user_data["updated_at"],
                )
            raise Exception("Failed to create user")
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    async def store_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Store refresh token in database"""
        try:
            client = await self._get_client()
            await client.table("refresh_tokens").insert({
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "user_agent": user_agent,
                "ip_address": ip_address,
            }).execute()
        except Exception as e:
            logger.error(f"Error storing refresh token: {e}", exc_info=True)
            raise

    async def get_refresh_token(self, token_hash: str) -> Optional[dict]:
        """Get refresh token by hash"""
        try:
            client = await self._get_client()
            result = await client.table("refresh_tokens").select("*").eq(
                "token_hash", token_hash
            ).gte("expires_at", self._get_current_time()).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting refresh token: {e}", exc_info=True)
            return None

    async def update_refresh_token_usage(self, token_id: str, last_used_at: str) -> None:
        """Update refresh token last usage time"""
        try:
            client = await self._get_client()
            await client.table("refresh_tokens").update({
                "last_used_at": last_used_at
            }).eq("id", token_id).execute()
        except Exception as e:
            logger.error(f"Error updating refresh token usage: {e}", exc_info=True)

    async def delete_refresh_token(self, token_hash: str) -> None:
        """Delete a refresh token"""
        try:
            client = await self._get_client()
            await client.table("refresh_tokens").delete().eq(
                "token_hash", token_hash
            ).execute()
        except Exception as e:
            logger.error(f"Error deleting refresh token: {e}", exc_info=True)

    async def delete_user_refresh_tokens(self, user_id: str) -> None:
        """Delete all refresh tokens for a user"""
        try:
            client = await self._get_client()
            await client.table("refresh_tokens").delete().eq(
                "user_id", user_id
            ).execute()
        except Exception as e:
            logger.error(f"Error deleting user refresh tokens: {e}", exc_info=True)

    def _get_current_time(self) -> str:
        """Get current time in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
