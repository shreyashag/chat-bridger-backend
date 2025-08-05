from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables"""

    # API Configuration
    api_title: str = "Actors API"
    api_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    log_file: str = "logs/actors.log"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Authentication Configuration
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # 30 minutes default

    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # Auth-specific Supabase Configuration (if different from main)
    supabase_auth_url: Optional[str] = None
    supabase_auth_key: Optional[str] = None

    # Sessions-specific Supabase Configuration (if different from main)
    sessions_supabase_url: Optional[str] = None
    sessions_supabase_key: Optional[str] = None

    # OpenAI configuration (if needed)
    openai_api_key: Optional[str] = None

    # OpenRouter configuration
    openrouter_key: Optional[str] = None

    # MCP Server URLs (optional - will use defaults if not provided)
    weather_mcp_server_url: Optional[str] = None
    time_mcp_server_url: Optional[str] = None

    # Tracing configuration (optional)
    openai_tracing_api_key: Optional[str] = None

    # Additional API keys (optional)
    perplexity_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    model_config = {
        "env_file": [
            Path(__file__).parent.parent / ".env.local",  # Local dev keys (will be missing in Docker)
        ],
        "case_sensitive": False,
        "env_ignore_empty": True,  # Ignore missing env files
        # "extra": "ignore"
    }

    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("debug", mode="before")
    def validate_debug(cls, v):
        """Convert string boolean to actual boolean"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @field_validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v):
        """Validate JWT secret key is provided"""
        if not v:
            raise ValueError("JWT_SECRET_KEY environment variable is required for security")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")
        return v

    @property
    def auth_supabase_url(self) -> str:
        """Get Supabase URL for auth (fallback to main URL)"""
        return self.supabase_auth_url or self.supabase_url

    @property
    def auth_supabase_key(self) -> str:
        """Get Supabase key for auth (fallback to main key)"""
        return self.supabase_auth_key or self.supabase_key

    @property
    def sessions_url(self) -> str:
        """Get Supabase URL for sessions (fallback to main URL)"""
        return self.sessions_supabase_url or self.supabase_url

    @property
    def sessions_key(self) -> str:
        """Get Supabase key for sessions (fallback to main key)"""
        return self.sessions_supabase_key or self.supabase_key


@lru_cache()
def get_config() -> Config:
    """Get cached application configuration"""
    return Config()
