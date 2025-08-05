from agents import Agent, ModelSettings

from src.core.agent_key import AgentKey
from src.core.mcp_manager import get_mcp_servers
from src.core.model_factory import create_model_by_key
from src.tooling.tools import (
    calculator,
    get_weather,
    get_latitude_and_longitude,
    get_current_time,
    date_calculator,
    date_difference,
    unit_converter,
    currency_converter,
    get_stock_price,
    get_stock_info_yfinance,
)


async def _create_chat_title_renamer():
    """Create chat title renamer agent."""
    model = create_model_by_key("cheap_model")

    return Agent(
        name="Chat title renamer",
        instructions="You are an expert at providing meaningful titles for the given chat",
        model=model,
        tools=[],
        model_settings=ModelSettings(temperature=0.3, max_tokens=3000),
    )


async def _create_history_tutor():
    """Create history tutor agent."""
    model = create_model_by_key("default")
    tools = [
        calculator,
        get_current_time,
        date_calculator,
        date_difference,
    ]

    return Agent(
        name="History Tutor",
        handoff_description="Specialist agent for history questions",
        instructions="You provide help with history problems. Explain your reasoning at each step and include examples",
        model=model,
        tools=tools,
        model_settings=ModelSettings(temperature=0.3, max_tokens=3000),
    )


async def _create_math_tutor():
    """Create math tutor agent."""
    model = create_model_by_key("default")
    tools = [
        calculator,
        unit_converter,
        currency_converter,
    ]

    return Agent(
        name="Math Tutor",
        handoff_description="Specialist agent for math questions",
        instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
        model=model,
        tools=tools,
        model_settings=ModelSettings(temperature=0.3, max_tokens=3000),
    )


async def _create_triage_agent():
    """Create triage agent with handoffs and agent tools."""
    model = create_model_by_key("default")
    mcp_servers = await get_mcp_servers(["time"])

    # Create the triage agent first
    agent = Agent(
        name="Triage Agent",
        instructions="""
        You are a helpful assistant.
        READ ALL THE RULES FIRST AND FOLLOW THEM CAREFULLY. 
        RULES: 
        1. Use available tools when needed, and be informative and assist the user with the queries. 
        2. If you use tools, first tell the user you will be using a tool. 
        3. Then, use the tool. 
        4. After that, summarise the tool output and use it to answer the user's query.
        """,
        model=model,
        tools=[],
        mcp_servers=mcp_servers,
        model_settings=ModelSettings(
            temperature=0.8,
            top_p=0.95,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            max_tokens=100 * 1024,
        ),
    )

    # Add handoffs
    # history_tutor = await get_agent_by_key(AgentKey.HISTORY_TUTOR)
    # math_tutor = await get_agent_by_key(AgentKey.MATH_TUTOR)
    # agent.handoffs = [history_tutor, math_tutor]

    # Add agent tools
    # history_tool = history_tutor.as_tool(
    #     tool_name="get_history_help",
    #     tool_description="Get help with historical questions and context",
    # )
    # math_tool = math_tutor.as_tool(
    #     tool_name="get_math_help",
    #     tool_description="Get help with mathematical problems and calculations",
    # )
    agent.tools = [
        calculator,
        get_weather,
        get_latitude_and_longitude,
        get_current_time,
        date_calculator,
        date_difference,
        unit_converter,
        currency_converter,
        get_stock_price,
        get_stock_info_yfinance,
        # history_tool, math_tool,
    ]

    return agent


# Agent factory functions
AGENT_FACTORIES = {
    AgentKey.CHAT_TITLE_RENAMER: _create_chat_title_renamer,
    AgentKey.HISTORY_TUTOR: _create_history_tutor,
    AgentKey.MATH_TUTOR: _create_math_tutor,
    AgentKey.TRIAGE_AGENT: _create_triage_agent,
}


async def get_agent_by_key(agent_key: AgentKey) -> Agent:
    """Create a fresh agent instance by its key."""
    if agent_key not in AGENT_FACTORIES:
        raise ValueError(
            f"Agent '{agent_key}' not found. Available agents: {list(AGENT_FACTORIES.keys())}"
        )

    # Create fresh instance every time
    return await AGENT_FACTORIES[agent_key]()
