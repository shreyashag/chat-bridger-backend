from typing import List

from fastapi import APIRouter, HTTPException

from src.api.models import AgentSummary
from src.core.agent_factory import AGENT_FACTORIES, get_agent_by_key
from src.core.agent_key import AgentKey

router = APIRouter()


@router.get(
    "/agents",
    response_model=List[AgentSummary],
    summary="Get Available Agents",
    description="Retrieve a list of all available AI agents with their configuration details",
    response_description="List of agent summaries containing keys, names, descriptions, and available tools",
    tags=["agents"],
    responses={
        200: {
            "description": "Successfully retrieved list of agents",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "key": "general_assistant",
                            "name": "General Assistant",
                            "description_for_user": "A versatile AI assistant capable of handling various tasks",
                            "tools": ["web_search", "file_operations", "calculator"],
                        },
                        {
                            "key": "code_reviewer",
                            "name": "Code Reviewer",
                            "description_for_user": "Specialized agent for reviewing and analyzing code",
                            "tools": ["code_analysis", "git_operations"],
                        },
                    ]
                }
            },
        },
        500: {
            "description": "Internal server error - failed to load agent configuration",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to load agent configuration"}
                }
            },
        },
    },
)
async def get_agents():
    """
    Get a list of all available agents with basic information.

    This endpoint returns metadata about all configured AI agents including:
    - Agent key (unique identifier)
    - Display name
    - User-facing description
    - Available tools

    Use this endpoint to populate agent selection interfaces or to discover
    available agents and their capabilities.
    """
    try:
        agents = []

        # Get all available agent keys from AGENT_FACTORIES
        for agent_key in AGENT_FACTORIES.keys():
            # Create agent instance to get its actual configuration
            agent = await get_agent_by_key(agent_key)

            # Determine user visibility based on agent key
            is_user_visible = agent_key == AgentKey.TRIAGE_AGENT

            # Only include agents that are user visible
            if not is_user_visible:
                continue

            # Extract tool names from agent's tools
            tool_names = []
            if hasattr(agent, "tools") and agent.tools:
                tool_names = [getattr(tool, "name", str(tool)) for tool in agent.tools]

            # Get description based on agent type
            description_for_user = ""
            if agent_key == AgentKey.TRIAGE_AGENT:
                description_for_user = "I determine which specialist agent can best help with your question and coordinate responses across different areas of expertise."
            elif agent_key == AgentKey.HISTORY_TUTOR:
                description_for_user = "I'm a specialist in history"
            elif agent_key == AgentKey.MATH_TUTOR:
                description_for_user = "I'm a specialist in mathematical problems and can help solve equations, explain concepts, and provide step-by-step solutions."

            agents.append(
                AgentSummary(
                    key=agent_key.value,
                    name=agent.name,
                    description_for_user=description_for_user,
                    tools=tool_names if tool_names else None,
                )
            )

        return agents
    except Exception as e:
        raise e
        raise HTTPException(status_code=500, detail=str(e))
