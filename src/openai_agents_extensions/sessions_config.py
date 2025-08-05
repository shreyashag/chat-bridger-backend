from dataclasses import dataclass
from typing import Optional

from ..config import get_config


@dataclass
class SessionsSupabaseConfig:
    """Configuration for Supabase sessions functionality."""

    supabase_url: str
    supabase_key: str

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize SessionsSupabaseConfig."""
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

    def validate(self) -> None:
        """Validate configuration values"""
        if not self.supabase_url.startswith(("http://", "https://")):
            raise ValueError("SUPABASE_URL must be a valid URL")

        if len(self.supabase_key) < 10:
            raise ValueError("SUPABASE_KEY appears to be invalid")


# Global configuration instance
_sessions_config: Optional[SessionsSupabaseConfig] = None


def get_sessions_config() -> SessionsSupabaseConfig:
    """Get the global sessions configuration instance"""
    global _sessions_config

    if _sessions_config is None:
        config = get_config()

        supabase_url = config.sessions_url
        supabase_key = config.sessions_key

        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not supabase_key:
            raise ValueError("SUPABASE_KEY environment variable is required")

        _sessions_config = SessionsSupabaseConfig(
            supabase_url=supabase_url, supabase_key=supabase_key
        )
        _sessions_config.validate()

    return _sessions_config
