from typing import Optional

from agents import Session


class ConversationContextManager:
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    async def get_message_with_context(self, current_message, memories=None):
        conversation = await self._session.get_items()
        """Merge conversation context with memories for agents"""
        if memories is None:
            memories = []

        memory_context = "\n".join([f"- {mem['memory']}" for mem in memories])

        return {
            "conversation_history": conversation,
            "user_memories": memory_context,
            "current_message": current_message,
        }
