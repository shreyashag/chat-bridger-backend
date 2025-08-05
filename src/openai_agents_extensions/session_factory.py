"""Session factory dependency for creating Supabase sessions."""

from typing import Optional

from src.logging_config import get_logger
from .sessions_config import get_sessions_config
from .supabase_session import SupabaseSession

logger = get_logger(__name__)


class SessionFactory:
    """Factory for creating Supabase sessions with pre-configured settings."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize the session factory with Supabase configuration.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        logger.debug("SessionFactory initialized")

    async def create_session(self, session_id: str, user_id: str) -> SupabaseSession:
        """Create a new Supabase session.

        Args:
            session_id: Unique identifier for the conversation session
            user_id: User identifier for RLS filtering

        Returns:
            Configured SupabaseSession instance
        """
        return await SupabaseSession.create(
            session_id=session_id,
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
            user_id=user_id,
        )


# Global session factory instance
_session_factory: Optional[SessionFactory] = None


def get_session_factory() -> SessionFactory:
    """Get the global session factory instance."""
    global _session_factory

    if _session_factory is None:
        config = get_sessions_config()
        _session_factory = SessionFactory(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_key,
        )
        logger.info("Global session factory created")

    return _session_factory


def get_session_factory_dependency() -> SessionFactory:
    """FastAPI dependency for getting the session factory."""
    return get_session_factory()


async def close_session_factory():
    """Close the session factory and cleanup connections."""
    global _session_factory

    if _session_factory is not None:
        # Close the connection pool used by SupabaseSession
        await SupabaseSession.close_connection_pool()
        _session_factory = None
        logger.info("Session factory closed")
