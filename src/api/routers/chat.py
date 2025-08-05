from agents import Agent
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse

from src.api.auth.dependencies import get_user_id
from src.api.docs.api_docs import SEND_MESSAGE_RESPONSES
from src.api.models import (
    MessageRequest,
    ConversationListResponse,
)
from src.api.models.responses import (
    DeleteConversationResponse,
    DeleteAllConversationsResponse,
    GetConversationResponse,
)
from src.services.chat_service import ChatService
from src.core.agent_factory import get_agent_by_key
from src.core.agent_key import AgentKey
from src.core.agent_loop import AgentLoop
from src.core.event_handlers import EventProcessor
from src.logging_config import get_logger
from src.openai_agents_extensions.session_factory import (
    get_session_factory_dependency,
    SessionFactory,
)
from src.services.conversation_context_manager import ConversationContextManager
from src.services.title_renamer import ChatTitleRenamer

logger = get_logger(__name__)

router = APIRouter()

# Chat service will be created per request for proper isolation


@router.post(
    "/chat/send_message",
    response_model=None,
    summary="Send Message to Agent",
    description="Send a message to an AI agent and receive a response within a session context",
    response_description="Agent response containing the generated message and session ID, or streaming NDJSON events",
    tags=["chat"],
    responses=SEND_MESSAGE_RESPONSES,
)
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory_dependency),
):
    """
    Send a message to an AI agent and receive a response, or continue after client tool execution.

    This unified endpoint handles both initial messages and continuation after client tool execution.
    It automatically detects the request type based on the presence of tool_results.

    **Request Parameters:**
    - `message`: The user's message/question to send to the agent (required for initial messages)
    - `session_id`: Unique identifier for the conversation session
    - `agent_key`: (Optional) Specific agent to use; if not provided, uses session default
    - `client_tools`: (Optional) List of client tools available for remote execution
    - `tool_results`: (Optional) Results from client tool executions (for continuation)

    **Initial Message Flow:**
    When `tool_results` is not provided, this acts as an initial message:
    - The agent processes the message with available tools
    - If a client tool is called, streaming stops with `client_tool_execution_required` event
    - Client executes the tool and calls this endpoint again with `tool_results`

    **Continuation Flow:**
    When `tool_results` is provided, this continues the conversation:
    - The tool results are added to the session history
    - The agent continues from where it left off
    - May result in additional client tool calls if needed

    **Response:**
    - NDJSON stream with structured events including:
      - `text_delta`: Text chunks for the final response
      - `agent_updated`: Agent state changes
      - `tool_call`: Tool invocations
      - `tool_output`: Tool execution results
      - `client_tool_execution_required`: Signals client tool execution needed
      - `message_output`: Complete message outputs
      - `done`: Stream completion marker

    **Session Management:**
    - Sessions maintain conversation context across multiple messages and tool executions
    - Each session is associated with a specific agent
    - Session data is persisted to maintain conversation history

    **Client Tool Pattern:**
    1. Send initial message with `client_tools` defined
    2. Agent may call client tool, stream returns `client_tool_execution_required`
    3. Client executes tool locally
    4. Client sends same request with `tool_results` filled and `message` empty
    5. Agent continues with tool results and completes response
    """
    try:
        logger.info(
            f"Processing message request - User: {user_id}, Session: {request.session_id}, Agent: {request.agent_key}, Stream: {request.stream}"
        )
        # Create session using the injected session factory
        session = await session_factory.create_session(
            session_id=request.session_id,
            user_id=user_id,
        )
        # Use the agent key from the request
        try:
            agent_key = AgentKey(request.agent_key)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid agent key: {request.agent_key}"
            )

        agent: Agent = await get_agent_by_key(agent_key)
        conversation_manager = ConversationContextManager(session)

        # Add background task to generate title after streaming response
        background_tasks.add_task(
            ChatTitleRenamer.generate_title_in_background_and_update,
            request.session_id,
            user_id,
        )

        # Determine if this is a continuation (has tool results)
        is_continuation = bool(request.tool_results)

        if is_continuation:
            # Continue after client tool execution
            stream = AgentLoop.continue_after_client_tools(
                agent,
                EventProcessor(),
                conversation_manager,
                request.tool_results,
                request.client_tools,
            )
        else:
            # Initial message
            stream = AgentLoop.run_agent_stream(
                agent,
                EventProcessor(),
                conversation_manager,
                request.message,
                request.client_tools,
            )

        return StreamingResponse(stream, media_type="application/x-ndjson")

    except Exception as e:
        logger.error(
            f"Error processing message request - User: {user_id}, Session: {request.session_id}, Error: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/chat",
    response_model=ConversationListResponse,
    summary="List Conversations",
    description="Retrieve a list of conversations from Supabase with optional filtering and pagination",
    response_description="List of conversations with metadata",
    tags=["chat"],
)
async def list_conversations(
    user_id: str = Depends(get_user_id),
    is_archived: bool = False,
    limit: int = 20,
    offset: int = 0,
):
    """
    Retrieve a list of conversations from Supabase.

    This endpoint fetches conversations from the database with optional filtering
    and pagination, ordered by last update time (most recent first).

    **Query Parameters:**
    - `is_archived`: Filter by archived status (default: False)
    - `limit`: Maximum number of conversations to return (default: 20)
    - `offset`: Number of conversations to skip (default: 0)

    **Response:**
    - `conversations`: List of conversation summaries with metadata
    - `total`: Total number of conversations found
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.list_conversations(
            user_id, is_archived, limit, offset
        )

        # Convert to API response format
        conversations = []
        for conv in result.conversations:
            conversations.append(
                {
                    "id": conv.id,
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "is_archived": conv.is_archived,
                    "is_starred": conv.is_starred,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                }
            )

        return ConversationListResponse(conversations=conversations, total=result.total)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch conversations: {str(e)}"
        )


@router.delete(
    "/chat/{session_id}",
    response_model=DeleteConversationResponse,
    summary="Delete Specific Conversation",
    description="Delete a specific conversation and all its messages",
    response_description="Success confirmation",
    tags=["chat"],
)
async def delete_conversation(session_id: str, user_id: str = Depends(get_user_id)):
    """
    Delete a specific conversation and all its messages.

    This endpoint removes a conversation and all associated messages from the database.
    Only the conversation owner can delete their conversations.

    **Parameters:**
    - `session_id`: The session ID of the conversation to delete

    **Response:**
    - Success message confirming deletion
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.delete_conversation(session_id, user_id)
        return DeleteConversationResponse(message=result.message)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete conversation: {str(e)}"
        )


@router.delete(
    "/chat",
    response_model=DeleteAllConversationsResponse,
    summary="Delete All Conversations",
    description="Delete all conversations and messages for the authenticated user",
    response_description="Success confirmation with count",
    tags=["chat"],
)
async def delete_all_conversations(user_id: str = Depends(get_user_id)):
    """
    Delete all conversations and messages for the authenticated user.

    This endpoint removes all conversations and associated messages from the database
    for the current user. This action cannot be undone.

    **Response:**
    - Success message with count of deleted conversations
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.delete_all_conversations(user_id)
        return DeleteAllConversationsResponse(
            message=result.message, deleted_count=result.deleted_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete conversations: {str(e)}"
        )


@router.get(
    "/chat/{session_id}",
    response_model=GetConversationResponse,
    summary="Get Conversation",
    description="Get a specific conversation by session ID with reverse pagination (last 10 messages by default)",
    response_description="The conversation details and messages",
    tags=["chat"],
)
async def get_conversation(
    session_id: str,
    user_id: str = Depends(get_user_id),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get a specific conversation by session ID with reverse pagination.

    This endpoint is used to load an existing conversation with its messages.
    By default, it loads the last 10 messages (reverse paginated).
    Only the conversation owner can get their conversations.

    **Parameters:**
    - `session_id`: The session ID of the conversation to retrieve
    - `limit`: Maximum number of messages to return (default: 10)
    - `offset`: Number of messages to skip from the end (default: 0)

    **Response:**
    - Conversation details and messages with pagination info
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.get_conversation(session_id, user_id, limit, offset)

        # Convert to API response format
        messages = []
        for msg in result.messages:
            # Parse message_data JSON and extract role
            parsed_content = {}
            role = "assistant"  # default

            try:
                import json

                parsed_content = (
                    json.loads(msg.message_data)
                    if isinstance(msg.message_data, str)
                    else msg.message_data
                )

                # Extract role from parsed content
                role = parsed_content.get("role", "assistant")

            except (json.JSONDecodeError, TypeError, AttributeError):
                # Fallback: create a basic structure
                parsed_content = {"content": str(msg.message_data)}
                role = "assistant"  # default fallback

            messages.append(
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "message_data": msg.message_data,
                    "content": parsed_content,
                    "role": role,
                    "user_id": msg.user_id,
                    "created_at": msg.created_at,
                }
            )

        conversation = {
            "id": result.conversation.id,
            "session_id": result.conversation.session_id,
            "title": result.conversation.title,
            "is_archived": result.conversation.is_archived,
            "is_starred": result.conversation.is_starred,
            "created_at": result.conversation.created_at,
            "updated_at": result.conversation.updated_at,
        }

        return GetConversationResponse(
            conversation=conversation,
            messages=messages,
            total_messages=result.total_messages,
            has_more=result.has_more,
        )

    except ValueError as e:
        raise e
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversation: {str(e)}"
        )


@router.post(
    "/chat/{session_id}/archive",
    response_model=DeleteConversationResponse,
    summary="Archive Conversation",
    description="Archive a specific conversation by session ID",
    response_description="Success confirmation",
    tags=["chat"],
)
async def archive_conversation(session_id: str, user_id: str = Depends(get_user_id)):
    """
    Archive a specific conversation by session ID.

    This endpoint marks a conversation as archived, which will exclude it from
    the regular conversation list. Only the conversation owner can archive their conversations.

    **Parameters:**
    - `session_id`: The session ID of the conversation to archive

    **Response:**
    - Success message confirming archival
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.archive_conversation(session_id, user_id)
        return DeleteConversationResponse(message=result.message)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to archive conversation: {str(e)}"
        )


@router.post(
    "/chat/{session_id}/star",
    response_model=DeleteConversationResponse,
    summary="Star Conversation",
    description="Star a specific conversation by session ID",
    response_description="Success confirmation",
    tags=["chat"],
)
async def star_conversation(session_id: str, user_id: str = Depends(get_user_id)):
    """
    Star a specific conversation by session ID.

    This endpoint marks a conversation as starred, which can be used to highlight
    important conversations. Only the conversation owner can star their conversations.

    **Parameters:**
    - `session_id`: The session ID of the conversation to star

    **Response:**
    - Success message confirming starring
    """
    try:
        # Create request-scoped chat service for proper isolation
        chat_service = ChatService()
        result = await chat_service.star_conversation(session_id, user_id)
        return DeleteConversationResponse(message=result.message)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to star conversation: {str(e)}"
        )
