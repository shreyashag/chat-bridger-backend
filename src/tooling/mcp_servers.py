from typing import List, Union

from agents.mcp import (
    MCPServerSse,
    MCPServerStdio,
    MCPServerStreamableHttp,
    MCPServerStdioParams,
)

from src.config import get_config
from src.logging_config import get_logger

logger = get_logger(__name__)

# No caching for MCP servers - create fresh instances each time


async def _create_weather_us():
    config = get_config()
    weather_server_url = config.weather_mcp_server_url or "http://localhost:11000/sse"
    server = MCPServerSse(
        params={
            "url": weather_server_url,
            "headers": {},
        },
        cache_tools_list=True,
        name="weather_us",
        client_session_timeout_seconds=30,
    )
    await server.connect()
    return server


async def _create_time():
    config = get_config()
    time_server_url = config.time_mcp_server_url or "http://localhost:11001/sse"
    server = MCPServerSse(
        params={
            "url": time_server_url,
            "headers": {},
        },
        cache_tools_list=True,
        name="time",
        client_session_timeout_seconds=30,
    )
    await server.connect()
    return server


async def _create_context7():
    server = MCPServerStreamableHttp(
        params={
            "url": "https://mcp.context7.com/mcp",
            "headers": {},
        },
        cache_tools_list=False,
        name="context7",
    )
    await server.connect()
    return server


async def _create_perplexity_ask():
    server = MCPServerStdio(
        params=MCPServerStdioParams(
            command="npx",
            args=["-y", "server-perplexity-ask"],
            env={"PERPLEXITY_API_KEY": get_config().perplexity_api_key or ""},
        ),
        cache_tools_list=True,
        name="perplexity-ask",
    )
    await server.connect()
    return server


# MCP server factory functions
MCP_SERVER_FACTORIES = {
    "weather_us": _create_weather_us,
    "time": _create_time,
    "context7": _create_context7,
    "perplexity-ask": _create_perplexity_ask,
}


async def create_mcp_servers(
    server_refs: List[str],
) -> List[Union[MCPServerSse, MCPServerStdio, MCPServerStreamableHttp]]:
    """Create and connect fresh MCP server instances."""
    if not server_refs:
        return []

    servers = []

    for server_ref in server_refs:
        if server_ref not in MCP_SERVER_FACTORIES:
            raise ValueError(
                f"MCP server '{server_ref}' not found. Available servers: {list(MCP_SERVER_FACTORIES.keys())}"
            )

        # Create fresh instance every time
        try:
            server = await MCP_SERVER_FACTORIES[server_ref]()
            servers.append(server)
        except Exception as e:
            logger.error(
                f"Failed to connect to MCP server '{server_ref}': {e}", exc_info=True
            )

    return servers
