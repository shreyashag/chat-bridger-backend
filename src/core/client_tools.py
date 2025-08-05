"""
Client tools management for converting client tool definitions to OpenAI Agent function tools.
"""

from typing import List, Any, Optional, Callable

from agents import FunctionTool
from agents.tool_context import ToolContext

from src.api.models.requests import ClientToolDefinition
from src.logging_config import get_logger

logger = get_logger(__name__)


def create_client_tool_function(
    client_tool: ClientToolDefinition, callback: Optional[Callable] = None
) -> FunctionTool:
    """
    Convert a ClientToolDefinition to a FunctionTool that handles client execution delegation.

    Args:
        client_tool: The client tool definition
        callback: Optional callback function to call when the tool is invoked
    """

    async def client_tool_handler(ctx: ToolContext[Any], args: str) -> str:
        """Handle client tool invocation by returning structured pending result."""
        import json

        tool_call_id = ctx.tool_call_id
        try:
            parameters = json.loads(args)
        except json.JSONDecodeError:
            parameters = {}

        logger.info(
            f"Client tool {client_tool.name} invoked with parameters: {parameters}, call_id: {tool_call_id}"
        )

        # Return structured pending result for streaming detection
        return json.dumps({
            "status": "PENDING_CLIENT_EXECUTION",
            "tool_name": client_tool.name,
            "tool_call_id": tool_call_id,
            "parameters": parameters,
            "message": f"Waiting for client execution of {client_tool.name}"
        })

    # Use the client tool's params_schema or create a basic one
    params_schema = client_tool.params_schema or {
        "type": "object",
        "properties": {},
        "required": [],
    }

    return FunctionTool(
        name=client_tool.name,
        description=client_tool.description,
        params_json_schema=params_schema,
        on_invoke_tool=client_tool_handler,
    )


def convert_client_tools_to_function_tools(
    client_tools: Optional[List[ClientToolDefinition]],
    callback: Optional[Callable] = None,
) -> List[FunctionTool]:
    """
    Convert a list of ClientToolDefinition objects to FunctionTool objects.

    Args:
        client_tools: List of client tool definitions from the API request
        callback: Optional callback function to call when any client tool is invoked

    Returns:
        List of FunctionTool objects that can be added to an agent
    """
    if not client_tools:
        return []

    function_tools = []
    for client_tool in client_tools:
        try:
            function_tool = create_client_tool_function(client_tool, callback)
            function_tools.append(function_tool)
            logger.debug(f"Converted client tool {client_tool.name} to FunctionTool")
        except Exception as e:
            logger.error(
                f"Failed to convert client tool {client_tool.name}: {e}", exc_info=True
            )

    return function_tools
