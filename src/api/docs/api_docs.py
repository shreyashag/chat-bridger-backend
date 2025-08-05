"""
API documentation responses and examples.

This module contains the response schemas and examples for FastAPI endpoints.
"""

# Response examples and schemas for the send_message endpoint
SEND_MESSAGE_RESPONSES = {
    200: {
        "description": "Successfully processed message and received agent response",
        "content": {
            "application/json": {
                "example": {
                    "response": "Hello! I'm here to help you with your questions. How can I assist you today?",
                    "session_id": "session_123456",
                }
            },
            "application/x-ndjson": {
                "example": """{"type": "agent_updated", "data": {"agent_name": "Triage Agent"}}
{"type": "text_delta", "data": ""}
{"type": "text_delta", "data": ""}
{"type": "message_output", "data": {"content": ""}}
{"type": "tool_call", "data": {"tool_name": "unknown", "message": "Tool was called"}}
{"type": "tool_output", "data": {"output": "The product of 1232 and 3132 is 3,858,624."}}
{"type": "text_delta", "data": ""}
{"type": "text_delta", "data": "The"}
{"type": "text_delta", "data": " result"}
{"type": "text_delta", "data": " of"}
{"type": "text_delta", "data": " "}
{"type": "text_delta", "data": "123"}
{"type": "text_delta", "data": "2"}
{"type": "text_delta", "data": " multiplied"}
{"type": "text_delta", "data": " by"}
{"type": "text_delta", "data": " "}
{"type": "text_delta", "data": "313"}
{"type": "text_delta", "data": "2"}
{"type": "text_delta", "data": " is"}
{"type": "text_delta", "data": " "}
{"type": "text_delta", "data": "3"}
{"type": "text_delta", "data": ","}
{"type": "text_delta", "data": "858"}
{"type": "text_delta", "data": ","}
{"type": "text_delta", "data": "624"}
{"type": "text_delta", "data": "."}
{"type": "text_delta", "data": ""}
{"type": "text_delta", "data": ""}
{"type": "message_output", "data": {"content": "The result of 1232 multiplied by 3132 is 3,858,624."}}
{"type": "done", "data": {}}"""
            },
        },
    },
    400: {
        "description": "Bad request - invalid agent key or malformed request",
        "content": {
            "application/json": {
                "examples": {
                    "invalid_agent_key": {
                        "summary": "Invalid agent key",
                        "value": {
                            "detail": "Invalid agent key in session: invalid_key"
                        },
                    },
                    "missing_required_field": {
                        "summary": "Missing required field",
                        "value": {"detail": "Field required"},
                    },
                }
            }
        },
    },
    500: {
        "description": "Internal server error - failed to process message",
        "content": {
            "application/json": {
                "example": {"detail": "Failed to process message through agent"}
            }
        },
    },
}
