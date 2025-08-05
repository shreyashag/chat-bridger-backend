import json
from abc import ABC, abstractmethod
from typing import Dict, Any

from agents import ItemHelpers, RunItemStreamEvent, AgentUpdatedStreamEvent
from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseCreatedEvent,
    ResponseOutputItemAddedEvent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseOutputItemDoneEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseCompletedEvent,
)

from src.logging_config import get_logger

logger = get_logger(__name__)


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: Any) -> Dict[str, Any] | None:
        """Handle an event and return a response dict or None."""
        pass


class TextDeltaHandler(EventHandler):
    """Handles raw response text delta events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(event.data, ResponseTextDeltaEvent):
            return {"type": "text_delta", "data": event.data.delta}
        return None


class AgentUpdatedHandler(EventHandler):
    """Handles agent update events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if isinstance(event, AgentUpdatedStreamEvent):
            return {
                "type": "agent_updated",
                "data": {"agent_name": event.new_agent.name},
            }
        return None


class ToolCallHandler(EventHandler):
    """Handles tool call events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if isinstance(event, RunItemStreamEvent) and event.name == "tool_called":
            tool_name = "unknown"
            tool_args = {}
            call_id = None

            if hasattr(event.item, "raw_item") and event.item.raw_item:
                call_id = event.item.raw_item.call_id
                if hasattr(event.item.raw_item, "function"):
                    tool_name = event.item.raw_item.function.name
                    arguments = event.item.raw_item.function.arguments
                else:
                    tool_name = getattr(event.item.raw_item, "name", "unknown")
                    arguments = getattr(event.item.raw_item, "arguments", "{}")

                try:
                    tool_args = (
                        json.loads(arguments)
                        if isinstance(arguments, str)
                        else arguments
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to parse tool arguments: {arguments} - {e}",
                        exc_info=True,
                    )
                    tool_args = {}

            return {
                "type": "tool_call",
                "call_id": call_id,
                "data": {
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "message": f"Calling {tool_name}",
                },
            }
        return None


class ToolOutputHandler(EventHandler):
    """Handles tool output events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if isinstance(event, RunItemStreamEvent) and event.name == "tool_output":
            return {
                "type": "tool_output",
                "data": {
                    "call_id": event.item.raw_item["call_id"],
                    "output": str(event.item.output)
                    if hasattr(event.item, "output")
                    else "",
                },
            }
        return None


class MessageOutputHandler(EventHandler):
    """Handles message output events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if (
            isinstance(event, RunItemStreamEvent)
            and event.name == "message_output_created"
        ):
            return {
                "type": "message_output",
                "data": {"content": ItemHelpers.text_message_output(event.item)},
            }
        return None


class ResponseCreatedHandler(EventHandler):
    """Handles response creation events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(event.data, ResponseCreatedEvent):
            return {
                "type": "response_created",
                "data": {
                    "response_id": event.data.response.id,
                    "model": event.data.response.model,
                    "status": event.data.response.status,
                },
            }
        return None


class ResponseOutputItemAddedHandler(EventHandler):
    """Handles response output item added events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(
            event.data, ResponseOutputItemAddedEvent
        ):
            return {
                "type": "output_item_added",
                "data": {
                    "item_id": event.data.item.id,
                    "item_type": event.data.item.type,
                    "output_index": event.data.output_index,
                },
            }
        return None


class ResponseContentPartAddedHandler(EventHandler):
    """Handles response content part added events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(
            event.data, ResponseContentPartAddedEvent
        ):
            return {
                "type": "content_part_added",
                "data": {
                    "item_id": event.data.item_id,
                    "content_index": event.data.content_index,
                    "part_type": event.data.part.type,
                },
            }
        return None


class ResponseContentPartDoneHandler(EventHandler):
    """Handles response content part done events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(
            event.data, ResponseContentPartDoneEvent
        ):
            content = ""
            if hasattr(event.data.part, "text"):
                content = event.data.part.text

            return {
                "type": "content_part_done",
                "data": {
                    "item_id": event.data.item_id,
                    "content_index": event.data.content_index,
                    "content": content,
                },
            }
        return None


class ResponseOutputItemDoneHandler(EventHandler):
    """Handles response output item done events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(
            event.data, ResponseOutputItemDoneEvent
        ):
            content = ""
            if hasattr(event.data.item, "content") and event.data.item.content:
                # Extract text from content array
                for content_part in event.data.item.content:
                    if hasattr(content_part, "text"):
                        content += content_part.text

            return {
                "type": "output_item_done",
                "data": {
                    "item_id": event.data.item.id,
                    "status": event.data.item.status,
                    "content": content,
                },
            }
        return None


class HandoffRequestedHandler(EventHandler):
    """Handles handoff requested events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if isinstance(event, RunItemStreamEvent) and event.name == "handoff_requested":
            return {
                "type": "handoff_requested",
                "data": {
                    "message": "Agent handoff requested",
                    "item_id": getattr(event.item, "id", "unknown"),
                },
            }
        return None


class ReasoningItemCreatedHandler(EventHandler):
    """Handles reasoning item created events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if (
            isinstance(event, RunItemStreamEvent)
            and event.name == "reasoning_item_created"
        ):
            return {
                "type": "reasoning_created",
                "data": {
                    "message": "Reasoning step created",
                    "item_id": getattr(event.item, "id", "unknown"),
                },
            }
        return None


class McpApprovalRequestedHandler(EventHandler):
    """Handles MCP approval requested events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if (
            isinstance(event, RunItemStreamEvent)
            and event.name == "mcp_approval_requested"
        ):
            return {
                "type": "mcp_approval_requested",
                "data": {
                    "message": "MCP approval requested",
                    "item_id": getattr(event.item, "id", "unknown"),
                },
            }
        return None


class McpListToolsHandler(EventHandler):
    """Handles MCP list tools events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if isinstance(event, RunItemStreamEvent) and event.name == "mcp_list_tools":
            return {
                "type": "mcp_list_tools",
                "data": {
                    "message": "MCP tools listed",
                    "item_id": getattr(event.item, "id", "unknown"),
                },
            }
        return None


class ResponseFunctionCallArgumentsDeltaHandler(EventHandler):
    """Handles function call arguments delta events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(
            event.data, ResponseFunctionCallArgumentsDeltaEvent
        ):
            return {
                "type": "function_call_arguments_delta",
                "data": {
                    "delta": event.data.delta,
                    "item_id": event.data.item_id,
                    "output_index": event.data.output_index,
                },
            }
        return None


class ResponseCompletedHandler(EventHandler):
    """Handles response completed events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        if hasattr(event, "data") and isinstance(event.data, ResponseCompletedEvent):
            return {
                "type": "response_completed",
                "data": {
                    "response_id": event.data.response.id,
                    "model": event.data.response.model,
                    "status": getattr(event.data.response, "status", "completed"),
                    "usage": {
                        "input_tokens": event.data.response.usage.input_tokens
                        if event.data.response.usage
                        else 0,
                        "output_tokens": event.data.response.usage.output_tokens
                        if event.data.response.usage
                        else 0,
                        "total_tokens": event.data.response.usage.total_tokens
                        if event.data.response.usage
                        else 0,
                    }
                    if event.data.response.usage
                    else None,
                },
            }
        return None


class ClientToolCallHandler(EventHandler):
    """Handles client tool call events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        # This handler will be called manually by AgentLoop when client tools are invoked
        # The event will be a custom dict with client tool call information
        if isinstance(event, dict) and event.get("type") == "client_tool_call":
            return {
                "type": "client_tool_call",
                "data": {
                    "tool_name": event.get("tool_name"),
                    "parameters": event.get("parameters", {}),
                    "tool_call_id": event.get("tool_call_id"),
                    "session_id": event.get("session_id"),
                    "message": f"Client tool '{event.get('tool_name')}' requires execution on the client side",
                },
            }
        return None


class ExecutionPausedHandler(EventHandler):
    """Handles execution paused events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        # This handler will be called manually by AgentLoop when execution is paused
        if isinstance(event, dict) and event.get("type") == "execution_paused":
            return {"type": "execution_paused", "data": event.get("data", {})}
        return None


class ClientToolExecutionRequiredHandler(EventHandler):
    """Handles client tool execution required events."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        # This handler will be called manually by AgentLoop when client tool execution is required
        if (
            isinstance(event, dict)
            and event.get("type") == "client_tool_execution_required"
        ):
            return {
                "type": "client_tool_execution_required",
                "data": event.get("data", {}),
            }
        return None


class DoneHandler(EventHandler):
    """Handles done events to signal completion."""

    async def handle(self, event: Any) -> Dict[str, Any] | None:
        # This handler will be called manually by AgentLoop when execution is complete
        if isinstance(event, dict) and event.get("type") == "done":
            return {"type": "done", "data": None}
        return None


class EventProcessor:
    """Processes events using registered handlers."""

    def __init__(self):
        # Create explicit handler references
        self.text_delta_handler = TextDeltaHandler()
        self.agent_updated_handler = AgentUpdatedHandler()
        self.tool_call_handler = ToolCallHandler()
        self.tool_output_handler = ToolOutputHandler()
        self.message_output_handler = MessageOutputHandler()
        self.response_created_handler = ResponseCreatedHandler()
        self.response_output_item_added_handler = ResponseOutputItemAddedHandler()
        self.response_content_part_added_handler = ResponseContentPartAddedHandler()
        self.response_content_part_done_handler = ResponseContentPartDoneHandler()
        self.response_output_item_done_handler = ResponseOutputItemDoneHandler()
        self.handoff_requested_handler = HandoffRequestedHandler()
        self.reasoning_item_created_handler = ReasoningItemCreatedHandler()
        self.mcp_approval_requested_handler = McpApprovalRequestedHandler()
        self.mcp_list_tools_handler = McpListToolsHandler()
        self.response_function_call_arguments_delta_handler = (
            ResponseFunctionCallArgumentsDeltaHandler()
        )
        self.response_completed_handler = ResponseCompletedHandler()
        self.client_tool_call_handler = ClientToolCallHandler()
        self.execution_paused_handler = ExecutionPausedHandler()
        self.client_tool_execution_required_handler = (
            ClientToolExecutionRequiredHandler()
        )
        self.done_handler = DoneHandler()

        # Create event name to handler mapping
        self.run_item_handlers = {
            "tool_called": self.tool_call_handler,
            "tool_output": self.tool_output_handler,
            "message_output_created": self.message_output_handler,
            "handoff_requested": self.handoff_requested_handler,
            "reasoning_item_created": self.reasoning_item_created_handler,
            "mcp_approval_requested": self.mcp_approval_requested_handler,
            "mcp_list_tools": self.mcp_list_tools_handler,
        }

        # Create response data type to handler mapping
        self.response_data_handlers = {
            ResponseTextDeltaEvent: self.text_delta_handler,
            ResponseCreatedEvent: self.response_created_handler,
            ResponseOutputItemAddedEvent: self.response_output_item_added_handler,
            ResponseContentPartAddedEvent: self.response_content_part_added_handler,
            ResponseContentPartDoneEvent: self.response_content_part_done_handler,
            ResponseOutputItemDoneEvent: self.response_output_item_done_handler,
            ResponseFunctionCallArgumentsDeltaEvent: self.response_function_call_arguments_delta_handler,
            ResponseCompletedEvent: self.response_completed_handler,
        }

    async def process_event(self, event: Any) -> Dict[str, Any] | None:
        """Process an event using handler mappings."""
        # Handle client tool call events (custom dict events)
        if isinstance(event, dict) and event.get("type") == "client_tool_call":
            return await self.client_tool_call_handler.handle(event)

        # Handle execution paused events (custom dict events)
        if isinstance(event, dict) and event.get("type") == "execution_paused":
            return await self.execution_paused_handler.handle(event)

        # Handle client tool execution required events (custom dict events)
        if (
            isinstance(event, dict)
            and event.get("type") == "client_tool_execution_required"
        ):
            return await self.client_tool_execution_required_handler.handle(event)

        # Handle done events (custom dict events)
        if isinstance(event, dict) and event.get("type") == "done":
            return await self.done_handler.handle(event)

        # Handle AgentUpdatedStreamEvent
        if isinstance(event, AgentUpdatedStreamEvent):
            return await self.agent_updated_handler.handle(event)

        # Handle RunItemStreamEvent using name mapping
        if isinstance(event, RunItemStreamEvent):
            handler = self.run_item_handlers.get(event.name)
            if handler:
                return await handler.handle(event)

        # Handle raw response events using type mapping
        if hasattr(event, "data"):
            handler = self.response_data_handlers.get(type(event.data))
            if handler:
                return await handler.handle(event)

        # Log unhandled events for debugging
        event_type = getattr(event, "type", type(event).__name__)
        event_name = getattr(event, "name", "unknown")
        logger.debug(f"Unhandled event - type: {event_type}, name: {event_name}")
        return None
