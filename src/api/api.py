from agents import set_tracing_disabled
from fastapi import FastAPI

from src.api.auth.router import router as auth_router
from src.api.routers import messages_router, agents_router, health_router, tools_router
from src.config import get_config
from src.core.mcp_manager import MCPManager
from src.logging_config import setup_logging, get_logger

# Initialize logging first
setup_logging()
logger = get_logger(__name__)

# For Agents SDK
set_tracing_disabled(disabled=True)

# Get configuration
config = get_config()
logger.info(
    f"Starting {config.api_title} v{config.api_version} in {'debug' if config.debug else 'production'} mode"
)

# Create FastAPI app
app = FastAPI(title=config.api_title, version=config.api_version)

# Add middlewares
# add_cors_middleware(app)  # CORS disabled


@app.on_event("startup")
async def startup_event():
    """Initialize MCP manager on application startup."""
    try:
        logger.info("Initializing MCP connections...")
        await MCPManager.get_instance()
        logger.info("MCP connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP connections: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup MCP connections on application shutdown."""
    try:
        logger.info("Shutting down MCP connections...")
        await MCPManager.shutdown()
        logger.info("MCP connections shut down successfully")
    except Exception as e:
        logger.error(f"Error during MCP shutdown: {e}", exc_info=True)


# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(agents_router)
app.include_router(tools_router)

logger.info("All routers registered successfully")
