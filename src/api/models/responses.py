from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """
    Response model for agent message processing.

    This model defines the structure of responses returned from the /send_message endpoint
    after an AI agent has processed a user's message.
    """

    response: str = Field(
        ...,
        description="The AI agent's generated response to the user's message",
        examples=[
            "I'd be happy to help with your project! Could you provide more details about what you're working on?"
        ],
    )

    session_id: str = Field(
        ...,
        description="The session ID used for this interaction, maintaining conversation context",
        examples=["session_123456"],
    )


class AgentSummary(BaseModel):
    """
    Summary model for AI agent information.

    This model provides metadata about available AI agents, including their
    capabilities and configuration details.
    """

    key: str = Field(
        ...,
        description="Unique identifier for the agent",
        examples=["general_assistant"],
    )

    name: str = Field(
        ...,
        description="Human-readable display name for the agent",
        examples=["General Assistant"],
    )

    description_for_user: str | None = Field(
        None,
        description="User-facing description of the agent's purpose and capabilities",
        examples=[
            "A versatile AI assistant capable of handling various tasks including research, writing, and problem-solving"
        ],
    )

    tools: List[str] | None = Field(
        None,
        description="List of available tools that the agent can use",
        examples=["web_search", "file_operations", "calculator", "code_analysis"],
    )


class ConversationSummary(BaseModel):
    """
    Summary model for conversation/chat information.

    This model represents a conversation session with metadata.
    """

    id: str = Field(
        ...,
        description="Unique identifier for the conversation",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    session_id: str = Field(
        ...,
        description="Session identifier for the conversation",
        examples=["session_123456"],
    )

    title: str = Field(
        ..., description="Title of the conversation", examples=["New Conversation"]
    )

    is_archived: bool = Field(
        False,
        description="Whether the conversation is archived",
        examples=[False],
    )

    is_starred: bool = Field(
        False,
        description="Whether the conversation is starred",
        examples=[False],
    )

    created_at: datetime = Field(..., description="When the conversation was created")

    updated_at: datetime = Field(
        ..., description="When the conversation was last updated"
    )


class ConversationListResponse(BaseModel):
    """
    Response model for listing conversations.
    """

    conversations: List[ConversationSummary] = Field(
        ...,
        description="List of conversations",
        examples=[
            {
                "id": "c31ddbcc-e57e-4820-bb93-aad969e1b7db",
                "session_id": "temp_session",
                "title": "New Chat",
                "created_at": "2025-07-17T11:10:34.677042Z",
                "updated_at": "2025-07-17T11:10:34.677042Z",
            }
        ],
    )

    total: int = Field(..., description="Total number of conversations", examples=[1])


class DeleteConversationResponse(BaseModel):
    """Response model for deleting a specific conversation."""

    message: str = Field(
        ...,
        description="Success message confirming deletion",
        examples=["Conversation session_123456 deleted successfully"],
    )


class DeleteAllConversationsResponse(BaseModel):
    """Response model for deleting all conversations."""

    message: str = Field(
        ...,
        description="Success message for bulk deletion",
        examples=["Successfully deleted all conversations"],
    )
    deleted_count: int = Field(
        ..., description="Number of conversations deleted", examples=[5]
    )


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""

    id: str = Field(
        ...,
        description="Unique identifier for the message",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    session_id: str = Field(
        ...,
        description="Session identifier for the conversation",
        examples=["session_123456"],
    )

    message_data: str = Field(
        ...,
        description="The actual message content (raw JSON)",
        examples=['{"role": "user", "content": "Hello, how can I help you today?"}'],
    )

    content: dict = Field(
        ...,
        description="The parsed message content as JSON object",
        examples=[{"role": "user", "content": "Hello, how can I help you today?"}],
    )

    role: str = Field(
        ...,
        description="The sender role (user or assistant)",
        examples=["user", "assistant"],
    )

    user_id: str = Field(
        ...,
        description="User identifier who sent the message",
        examples=["user_123"],
    )

    created_at: datetime = Field(..., description="When the message was created")


class GetConversationResponse(BaseModel):
    """Response model for getting a specific conversation."""

    conversation: ConversationSummary = Field(
        ...,
        description="The conversation details",
    )

    messages: List[ChatMessageResponse] = Field(
        ...,
        description="List of messages in the conversation",
    )

    total_messages: int = Field(
        ...,
        description="Total number of messages in the conversation",
        examples=[10],
    )

    has_more: bool = Field(
        ...,
        description="Whether there are more messages (for pagination)",
        examples=[False],
    )
