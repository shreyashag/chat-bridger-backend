import json
from datetime import datetime, timezone
from typing import List, Optional, Dict

from agents import TResponseInputItem
from agents.memory.session import SessionABC, Session
from supabase import acreate_client, AsyncClient

from src.logging_config import get_logger

logger = get_logger(__name__)

# Global connection pool for Supabase clients
_connection_pool: Dict[str, AsyncClient] = {}


class SupabaseSession(SessionABC, Session):
    """Supabase-backed session implementation following the Session protocol."""

    def __init__(
        self,
        session_id: str,
        supabase_url: str,
        supabase_key: str,
        user_id: str,
        conversations_table: str = "conversations",
        messages_table: str = "messages",
    ):
        """Initialize the Supabase session.

        Args:
            session_id: Unique identifier for the conversation session
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            user_id: User identifier for RLS filtering
            conversations_table: Name of the conversations table. Defaults to 'conversations'
            messages_table: Name of the messages table. Defaults to 'messages'
        """
        self.session_id = session_id
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.user_id = user_id
        self.conversations_table = conversations_table
        self.messages_table = messages_table
        self.supabase: Optional[AsyncClient] = None
        self._initialized = False

    async def _get_or_create_client(self) -> AsyncClient:
        """Get or create a client from the connection pool."""
        pool_key = f"{self.supabase_url}:{self.supabase_key}"

        if pool_key not in _connection_pool:
            logger.debug(f"Creating new Supabase client for pool key: {pool_key}")
            _connection_pool[pool_key] = await acreate_client(
                self.supabase_url, self.supabase_key
            )

        return _connection_pool[pool_key]

    @classmethod
    async def close_connection_pool(cls):
        """Close all connections in the pool (for cleanup during app shutdown)."""
        global _connection_pool

        for pool_key, client in _connection_pool.items():
            try:
                logger.debug(f"Closing Supabase client for pool key: {pool_key}")
                # Call sign_out to properly close connections as per Supabase docs
                client.auth.sign_out()
            except Exception as e:
                logger.warning(f"Error closing client for {pool_key}: {e}")

        _connection_pool.clear()
        logger.info("Supabase connection pool closed")

    async def _ensure_initialized(self):
        """Ensure the async client is initialized."""
        if not self._initialized:
            if self.supabase is None:
                self.supabase = await self._get_or_create_client()
            await self._load_or_create_session()
            self._initialized = True

    @classmethod
    async def create(
        cls,
        session_id: str,
        supabase_url: str,
        supabase_key: str,
        user_id: str,
        conversations_table: str = "conversations",
        messages_table: str = "messages",
    ):
        """Async factory method to create a SupabaseSession."""
        instance = cls(
            session_id=session_id,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            user_id=user_id,
            conversations_table=conversations_table,
            messages_table=messages_table,
        )
        await instance._ensure_initialized()
        return instance

    @staticmethod
    def _get_current_time():
        """Get current UTC time in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def _load_session(self) -> bool:
        """Load existing session data. Returns True if session exists, False otherwise"""
        try:
            existing_session = await (
                self.supabase.table(self.conversations_table)
                .select("*")
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .execute()
            )

            if existing_session.data:
                # Load existing session data
                session_data = existing_session.data[0]
                self.title = session_data.get("title", "New Chat")
                return True

            return False
        except Exception as e:
            logger.error(f"Error loading session: {e}", exc_info=True)
            return False

    async def _create_session(self):
        """Create a new session"""
        try:
            self.title = "New Chat"
            now = self._get_current_time()
            await (
                self.supabase.table(self.conversations_table)
                .insert(
                    {
                        "session_id": self.session_id,
                        "title": self.title,
                        "user_id": self.user_id,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            self.title = "New Chat"

    async def _load_or_create_session(self):
        """Load existing session data or create a new session"""
        # Try to load existing session first
        session_exists = await self._load_session()

        # If session doesn't exist, create a new one
        if not session_exists:
            await self._create_session()

    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        """Retrieve conversation history for this session."""
        await self._ensure_initialized()
        try:
            if limit is None:
                # Fetch all items in chronological order
                query = (
                    self.supabase.table(self.messages_table)
                    .select("message_data")
                    .eq("session_id", self.session_id)
                    .eq("user_id", self.user_id)
                    .order("created_at", desc=False)
                )
            else:
                # Fetch the latest N items in reverse chronological order, then reverse
                query = (
                    self.supabase.table(self.messages_table)
                    .select("message_data")
                    .eq("session_id", self.session_id)
                    .eq("user_id", self.user_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                )

            result = await query.execute()

            # Parse the stored JSON data back to TResponseInputItem format
            items = []
            for msg in result.data or []:
                message_data = msg.get("message_data")
                if isinstance(message_data, str):
                    try:
                        item = json.loads(message_data)
                        items.append(item)
                    except (json.JSONDecodeError, TypeError):
                        # Skip invalid JSON entries
                        continue

            # Reverse to get chronological order when using DESC
            if limit is not None:
                items = list(reversed(items))

            return items
        except Exception as e:
            logger.error(f"Error getting items: {e}", exc_info=True)
            return []

    def _is_empty_user_message(self, item: TResponseInputItem) -> bool:
        """Check if an item is an empty user message that should be filtered out."""
        if not isinstance(item, dict):
            return False

        # Only filter user messages
        if item.get("role") != "user":
            return False

        # Check if content is empty or whitespace-only
        content = item.get("content", "")
        if isinstance(content, str):
            return not content.strip()
        elif isinstance(content, list):
            # For list content, check if all text items are empty
            text_content = ""
            for content_item in content:
                if (
                    isinstance(content_item, dict)
                    and content_item.get("type") == "text"
                ):
                    text_content += content_item.get("text", "")
            return not text_content.strip()

        return False

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """Store new items for this session."""
        if not items:
            return

        await self._ensure_initialized()
        try:
            # Filter out empty user messages
            filtered_items = []
            filtered_count = 0

            for item in items:
                if self._is_empty_user_message(item):
                    filtered_count += 1
                    logger.debug(
                        f"Filtered out empty user message for session {self.session_id}"
                    )
                else:
                    filtered_items.append(item)

            if filtered_count > 0:
                logger.info(
                    f"Filtered out {filtered_count} empty user message(s) from session {self.session_id}"
                )

            # If all items were filtered out, just update timestamp and return
            if not filtered_items:
                await (
                    self.supabase.table(self.conversations_table)
                    .update({"updated_at": self._get_current_time()})
                    .eq("session_id", self.session_id)
                    .eq("user_id", self.user_id)
                    .execute()
                )
                return

            # Serialize each item to JSON string (exactly like SQLiteSession does)
            message_data = [
                {
                    "session_id": self.session_id,
                    "message_data": json.dumps(item),
                    "user_id": self.user_id,
                    "created_at": self._get_current_time(),
                }
                for item in filtered_items
            ]

            # Insert all items at once
            await (
                self.supabase.table(self.messages_table).insert(message_data).execute()
            )

            # Update session timestamp
            await (
                self.supabase.table(self.conversations_table)
                .update({"updated_at": self._get_current_time()})
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .execute()
            )

        except Exception as e:
            logger.error(f"Error adding items: {e}", exc_info=True)

    async def pop_item(self) -> dict | None:
        """Remove and return the most recent item from this session."""
        await self._ensure_initialized()
        try:
            # Get the most recent message
            result = await (
                self.supabase.table(self.messages_table)
                .select("id, message_data")
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return None

            message = result.data[0]

            # Delete the message
            await (
                self.supabase.table(self.messages_table)
                .delete()
                .eq("id", message["id"])
                .execute()
            )

            # Update session timestamp
            await (
                self.supabase.table(self.conversations_table)
                .update({"updated_at": self._get_current_time()})
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .execute()
            )

            # Parse the stored JSON data back to TResponseInputItem format
            message_data = message.get("message_data")
            if isinstance(message_data, str):
                try:
                    item = json.loads(message_data)
                    return item
                except (json.JSONDecodeError, TypeError):
                    # Return None for corrupted JSON entries
                    return None

            return None

        except Exception as e:
            logger.error(f"Error popping item: {e}", exc_info=True)
            return None

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        await self._ensure_initialized()
        try:
            # Delete all messages for this session
            await (
                self.supabase.table(self.messages_table)
                .delete()
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .execute()
            )

            # Update session timestamp
            await (
                self.supabase.table(self.conversations_table)
                .update({"updated_at": self._get_current_time()})
                .eq("session_id", self.session_id)
                .eq("user_id", self.user_id)
                .execute()
            )

        except Exception as e:
            logger.error(f"Error clearing session: {e}", exc_info=True)
