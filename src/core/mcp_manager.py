import asyncio
from typing import Dict, List, Union, Optional, Any

from agents.mcp import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp

from src.logging_config import get_logger
from src.tooling.mcp_servers import MCP_SERVER_FACTORIES

logger = get_logger(__name__)


class MCPServerProxy:
    """Proxy wrapper for MCP servers that prevents lifecycle management by agents."""

    def __init__(
        self, server: Union[MCPServerSse, MCPServerStdio, MCPServerStreamableHttp]
    ):
        self._server = server
        self._server_name = getattr(server, "name", "unknown")

    def __getattr__(self, name: str) -> Any:
        """Delegate all attribute access to the wrapped server, except lifecycle methods."""
        if name in ("disconnect", "close", "__del__"):
            # Prevent agents from closing the shared connection
            logger.debug(
                f"Prevented lifecycle method '{name}' call on shared MCP server '{self._server_name}'"
            )
            return self._noop
        return getattr(self._server, name)

    async def _noop(self, *args, **kwargs):
        """No-op method for lifecycle calls."""
        pass


class MCPManager:
    """Singleton manager for MCP server connections with connection pooling."""

    _instance: Optional["MCPManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if MCPManager._instance is not None:
            raise RuntimeError("MCPManager is a singleton. Use get_instance() instead.")
        self._servers: Dict[
            str, Union[MCPServerSse, MCPServerStdio, MCPServerStreamableHttp]
        ] = {}
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> "MCPManager":
        """Get the singleton instance of MCPManager."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """Initialize the MCP manager and create connections."""
        if self._initialized:
            return

        logger.info("Initializing MCP Manager...")

        # # Initialize commonly used servers
        # await self._connect_server("time")
        # # Add other servers as needed
        # await self._connect_server("weather_us")

        self._initialized = True
        logger.info("MCP Manager initialized successfully")

    async def _connect_server(self, server_name: str):
        """Connect to a specific MCP server."""
        if server_name in self._servers:
            logger.debug(f"MCP server '{server_name}' already connected")
            return self._servers[server_name]

        if server_name not in MCP_SERVER_FACTORIES:
            raise ValueError(f"Unknown MCP server: {server_name}")

        try:
            logger.info(f"Connecting to MCP server: {server_name}")
            server = await MCP_SERVER_FACTORIES[server_name]()
            self._servers[server_name] = server
            logger.info(f"Successfully connected to MCP server: {server_name}")
            return server
        except Exception as e:
            logger.error(
                f"Failed to connect to MCP server '{server_name}': {e}", exc_info=True
            )
            raise

    async def get_servers(self, server_names: List[str]) -> List[MCPServerProxy]:
        """Get MCP servers by names, connecting if necessary. Returns proxies to prevent lifecycle management."""
        servers = []

        for server_name in server_names:
            if server_name not in self._servers:
                await self._connect_server(server_name)
            # Wrap the server in a proxy to prevent agents from managing its lifecycle
            proxy = MCPServerProxy(self._servers[server_name])
            servers.append(proxy)

        return servers

    async def get_server(self, server_name: str) -> MCPServerProxy:
        """Get a single MCP server by name, connecting if necessary. Returns proxy to prevent lifecycle management."""
        if server_name not in self._servers:
            await self._connect_server(server_name)
        # Wrap the server in a proxy to prevent agents from managing its lifecycle
        return MCPServerProxy(self._servers[server_name])

    async def disconnect_server(self, server_name: str):
        """Disconnect a specific MCP server."""
        if server_name in self._servers:
            try:
                server = self._servers[server_name]
                if hasattr(server, "disconnect"):
                    await server.disconnect()
                elif hasattr(server, "close"):
                    await server.close()
                del self._servers[server_name]
                logger.info(f"Disconnected MCP server: {server_name}")
            except Exception as e:
                logger.error(
                    f"Error disconnecting MCP server '{server_name}': {e}",
                    exc_info=True,
                )

    async def disconnect_all(self):
        """Disconnect all MCP servers."""
        logger.info("Disconnecting all MCP servers...")

        for server_name in list(self._servers.keys()):
            await self.disconnect_server(server_name)

        self._servers.clear()
        self._initialized = False
        logger.info("All MCP servers disconnected")

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return server_name in self._servers

    def list_connected_servers(self) -> List[str]:
        """Get a list of currently connected server names."""
        return list(self._servers.keys())

    @classmethod
    async def shutdown(cls):
        """Shutdown the MCP manager and disconnect all servers."""
        if cls._instance is not None:
            await cls._instance.disconnect_all()
            cls._instance = None


# Convenience functions for backward compatibility
async def get_mcp_servers(server_names: List[str]) -> List[MCPServerProxy]:
    """Get MCP servers using the singleton manager."""
    manager = await MCPManager.get_instance()
    return await manager.get_servers(server_names)


async def get_mcp_server(server_name: str) -> MCPServerProxy:
    """Get a single MCP server using the singleton manager."""
    manager = await MCPManager.get_instance()
    return await manager.get_server(server_name)
