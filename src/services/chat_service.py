from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from supabase import acreate_client, AsyncClient

from src.openai_agents_extensions.sessions_config import get_sessions_config


class ChatConversation(BaseModel):
    """Chat conversation model"""

    id: str
    session_id: str
    title: str
    user_id: str
    is_archived: bool = False
    is_starred: bool = False
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    """Chat message model"""

    id: str
    session_id: str
    message_data: str
    user_id: str
    created_at: datetime


class ConversationListResult(BaseModel):
    """Result model for conversation list"""

    conversations: List[ChatConversation]
    total: int


class DeleteResult(BaseModel):
    """Result model for delete operations"""

    message: str
    deleted_count: Optional[int] = None


class ConversationResult(BaseModel):
    """Result model for get_conversation"""

    conversation: ChatConversation
    messages: List[ChatMessage]
    total_messages: int
    has_more: bool


class ChatService:
    """Service class for chat operations"""

    def __init__(self):
        self._client: Optional[AsyncClient] = None

    async def _get_client(self) -> AsyncClient:
        """Get or create Supabase client"""
        if self._client is None:
            session_config = get_sessions_config()
            self._client = await acreate_client(
                session_config.supabase_url, session_config.supabase_key
            )
        return self._client

    async def list_conversations(
        self, user_id: str, is_archived: bool = False, limit: int = 20, offset: int = 0
    ) -> ConversationListResult:
        """List conversations for a user with optional filtering and pagination"""
        client = await self._get_client()

        # Query conversations from database with filtering and pagination
        result = (
            await client.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_archived", is_archived)
            .order("updated_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        conversations = []
        for row in result.data or []:
            conversations.append(
                ChatConversation(
                    id=row["id"],
                    session_id=row["session_id"],
                    title=row["title"],
                    user_id=row["user_id"],
                    is_archived=row.get("is_archived", False),
                    is_starred=row.get("is_starred", False),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )

        return ConversationListResult(
            conversations=conversations, total=len(conversations)
        )

    async def delete_conversation(self, session_id: str, user_id: str) -> DeleteResult:
        """Delete a specific conversation"""
        client = await self._get_client()

        # First, verify the conversation exists and belongs to the user
        conversation_result = (
            await client.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conversation_result.data:
            raise ValueError("Conversation not found or access denied")

        # Delete the conversation (messages will be deleted automatically due to CASCADE)
        await (
            client.table("conversations")
            .delete()
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return DeleteResult(message=f"Conversation {session_id} deleted successfully")

    async def delete_all_conversations(self, user_id: str) -> DeleteResult:
        """Delete all conversations for a user"""
        client = await self._get_client()

        # First, get count of conversations to be deleted
        count_result = (
            await client.table("conversations")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )

        conversation_count = len(count_result.data) if count_result.data else 0

        if conversation_count == 0:
            return DeleteResult(
                message="No conversations found to delete", deleted_count=0
            )

        # Delete all conversations for the user (messages will be deleted automatically due to CASCADE)
        await client.table("conversations").delete().eq("user_id", user_id).execute()

        return DeleteResult(
            message="Successfully deleted all conversations",
            deleted_count=conversation_count,
        )

    async def archive_conversation(self, session_id: str, user_id: str) -> DeleteResult:
        """Archive a specific conversation"""
        client = await self._get_client()

        # First, verify the conversation exists and belongs to the user
        conversation_result = (
            await client.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conversation_result.data:
            raise ValueError("Conversation not found or access denied")

        # Archive the conversation
        await (
            client.table("conversations")
            .update({"is_archived": True})
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return DeleteResult(message=f"Conversation {session_id} archived successfully")

    async def star_conversation(self, session_id: str, user_id: str) -> DeleteResult:
        """Star a specific conversation"""
        client = await self._get_client()

        # First, verify the conversation exists and belongs to the user
        conversation_result = (
            await client.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conversation_result.data:
            raise ValueError("Conversation not found or access denied")

        # Star the conversation
        await (
            client.table("conversations")
            .update({"is_starred": True})
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return DeleteResult(message=f"Conversation {session_id} starred successfully")

    async def get_conversation(
        self, session_id: str, user_id: str, limit: int = 10, offset: int = 0
    ) -> ConversationResult:
        """Get a specific conversation with paginated messages (reverse pagination - last N messages)"""
        client = await self._get_client()

        # First, get the conversation details
        conversation_result = (
            await client.table("conversations")
            .select("*")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conversation_result.data:
            raise ValueError("Conversation not found or access denied")

        conversation_data = conversation_result.data[0]
        conversation = ChatConversation(
            id=conversation_data["id"],
            session_id=conversation_data["session_id"],
            title=conversation_data["title"],
            user_id=conversation_data["user_id"],
            is_archived=conversation_data.get("is_archived", False),
            is_starred=conversation_data.get("is_starred", False),
            created_at=conversation_data["created_at"],
            updated_at=conversation_data["updated_at"],
        )

        # Get total count of messages for this conversation
        total_count_result = (
            await client.table("messages")
            .select("id", count="exact")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        total_messages = total_count_result.count or 0

        # Get messages with reverse pagination (last N messages)
        # Order by created_at DESC to get the most recent messages first
        messages_result = (
            await client.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        messages = []
        for row in messages_result.data or []:
            messages.append(
                ChatMessage(
                    id=row["id"],
                    session_id=row["session_id"],
                    message_data=row["message_data"],
                    user_id=row["user_id"],
                    created_at=row["created_at"],
                )
            )

        # Reverse the messages to display them in chronological order
        messages.reverse()

        # Calculate if there are more messages
        has_more = (offset + limit) < total_messages

        return ConversationResult(
            conversation=conversation,
            messages=messages,
            total_messages=total_messages,
            has_more=has_more,
        )

    async def update_conversation_title(
        self, session_id: str, user_id: str, new_title: str
    ) -> DeleteResult:
        """Update the title of a specific conversation"""
        client = await self._get_client()

        # First, verify the conversation exists and belongs to the user
        conversation_result = (
            await client.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conversation_result.data:
            raise ValueError("Conversation not found or access denied")

        # Update the conversation title
        await (
            client.table("conversations")
            .update({"title": new_title})
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return DeleteResult(message=f"Conversation title updated to: {new_title}")
