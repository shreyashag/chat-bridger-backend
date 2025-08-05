from typing import List

from fastapi import APIRouter

from src.tooling.tools import AVAILABLE_TOOLS, ToolMetadata

router = APIRouter()


@router.get(
    "/tools",
    response_model=List[ToolMetadata],
    summary="List Available Tools",
    description="Retrieve a list of available tools in the system with their descriptions",
    response_description="List of tools with names and human-readable descriptions",
    tags=["tools"],
)
async def list_tools():
    """
    Retrieve a list of available tools in the system.

    This endpoint returns information about all tools that are currently
    available for use by agents in the system, including their names
    and human-readable descriptions.

    **Response:**
    - List of ToolMetadata objects containing:
      - name: The tool name
      - description: Human-readable description (if available)
    """
    tools = []
    for name, tool in AVAILABLE_TOOLS.items():
        metadata = getattr(tool, "tool_metadata", None)
        if metadata:
            # Create a new ToolMetadata with the name set
            tool_info = ToolMetadata(name=name, description=metadata.description)
            tools.append(tool_info)
        else:
            # Create a basic ToolMetadata with just the name
            tools.append(
                ToolMetadata(name=name, description="No description available")
            )
    return tools
