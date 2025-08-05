from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ClientToolDefinition(BaseModel):
    """Definition of a client tool available for remote execution."""

    name: str = Field(
        ...,
        description="Name of the tool (e.g., 'mobile:play_music')",
        examples=["mobile:play_music"],
    )

    description: str = Field(
        ...,
        description="Description of what the tool does",
        examples=["Play music on the mobile device"],
    )

    params_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON schema for the tool's parameters",
        examples=[
            {
                "type": "object",
                "properties": {
                    "song": {
                        "type": "string",
                        "description": "The name of the song to play",
                    },
                    "volume": {
                        "type": "integer",
                        "description": "Volume level (0-100)",
                    },
                },
                "required": ["song"],
            }
        ],
    )


class MessageRequest(BaseModel):
    """
    Request model for sending messages to AI agents.

    This model defines the structure for message requests sent to the /send_message endpoint.
    """

    message: str = Field(
        ...,
        description="The user's message or question to send to the AI agent",
        examples=["Hello, can you help me with my project?"],
    )

    session_id: str = Field(
        ...,
        description="Unique identifier for the conversation session to maintain context",
        examples=["session_123456"],
    )

    agent_key: str | None = Field(
        None,
        description="Agent key to specify which agent to use",
        examples=["triage_agent"],
    )

    stream: bool = Field(
        True,
        description="Whether to stream the response or return it all at once",
        examples=[True],
    )

    client_tools: Optional[List[ClientToolDefinition]] = Field(
        None,
        description="List of client tools available for remote execution",
        examples=[
            [
                {
                    "name": "mobile_play_music",
                    "description": "Play music on the mobile device",
                    "params_schema": {
                        "type": "object",
                        "properties": {
                            "song": {
                                "type": "string",
                                "description": "The name of the song to play",
                            },
                            "volume": {
                                "type": "integer",
                                "description": "Volume level (0-100)",
                            },
                        },
                        "required": ["song"],
                    },
                }
            ]
        ],
    )

    tool_results: Optional[List["ClientToolResult"]] = Field(
        None,
        description="Results from client tool executions (for continuation after client tool execution)",
        examples=[
            [
                {
                    "tool_call_id": "nMjjivBlE",
                    "tool_name": "mobile_play_music",
                    "result": "Successfully played 'Crazy Train' at volume 100",
                    "error": None,
                }
            ]
        ],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Play some music for me",
                "session_id": "session_123456",
                "agent_key": "triage_agent",
                "stream": True,
                "client_tools": [
                    {
                        "name": "mobile_play_music",
                        "description": "Play music on the mobile device",
                        "params_schema": {
                            "type": "object",
                            "properties": {
                                "song": {
                                    "type": "string",
                                    "description": "The name of the song to play",
                                },
                                "volume": {
                                    "type": "integer",
                                    "description": "Volume level (0-100)",
                                },
                            },
                            "required": ["song"],
                        },
                    },
                    {
                        "name": "mobile_send_sms",
                        "description": "Send SMS message",
                        "params_schema": {
                            "type": "object",
                            "properties": {
                                "phone": {
                                    "type": "string",
                                    "description": "Phone number to send SMS to",
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Message content to send",
                                },
                            },
                            "required": ["phone", "message"],
                        },
                    },
                ],
            }
        }
    }


class ClientToolResult(BaseModel):
    """Result of a client tool execution."""

    tool_call_id: str = Field(
        ...,
        description="The ID of the tool call this result corresponds to",
        examples=["nMjjivBlE"],
    )

    tool_name: str = Field(
        ...,
        description="Name of the tool that was executed",
        examples=["mobile:play_music"],
    )

    result: Optional[str] = Field(
        None,
        description="The result/output from the tool execution",
        examples=["Successfully played 'Crazy Train' at volume 100"],
    )

    error: Optional[str] = Field(
        None,
        description="Error message if the tool execution failed",
        examples=["Failed to play music: Device not connected"],
    )


class ClientToolResultRequest(BaseModel):
    """Request model for submitting client tool execution results."""

    session_id: str = Field(
        ...,
        description="Session ID where the tool was originally called",
        examples=["21376218jsdhdgfjdshf"],
    )

    tool_results: List[ClientToolResult] = Field(
        ...,
        description="List of tool execution results",
        examples=[
            [
                {
                    "tool_call_id": "nMjjivBlE",
                    "tool_name": "mobile:play_music",
                    "result": "Successfully played 'Crazy Train' at volume 100",
                    "error": None,
                }
            ]
        ],
    )

    client_tools: Optional[List[ClientToolDefinition]] = Field(
        None,
        description="List of client tools still available for the continuation",
        examples=[
            [
                {
                    "name": "mobile:play_music",
                    "description": "Play music on the mobile device",
                    "params_schema": {
                        "type": "object",
                        "properties": {
                            "song": {"type": "string"},
                            "volume": {"type": "integer"},
                        },
                        "required": ["song"],
                    },
                }
            ]
        ],
    )
