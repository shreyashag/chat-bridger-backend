import pytest
from agents import Agent

from src.core.agent_factory import get_agent_by_key
from src.core.agent_key import AgentKey


@pytest.mark.asyncio
@pytest.mark.parametrize("agent_key", list(AgentKey))
async def test_agent_get_by_key(agent_key: AgentKey):
    """Test that all agent keys can successfully create agents without failures."""
    agent: Agent = await get_agent_by_key(agent_key)

    assert agent is not None
    assert isinstance(agent, Agent)
    assert agent.name is not None
    assert len(agent.name) > 0


@pytest.mark.asyncio
async def test_agent_get_by_key_invalid():
    """Test that getting an invalid agent key raises ValueError."""
    with pytest.raises(
        ValueError, match="Agent 'invalid_agent' not found in configuration"
    ):
        # Type ignore needed since we're testing invalid input
        await get_agent_by_key("invalid_agent")  # type: ignore
