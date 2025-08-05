import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from src.config import get_config


def setup_logging(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
) -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_file: Path to log file. Defaults to logs/actors.log
        log_level: Logging level. Defaults to config.log_level
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    config = get_config()

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Set default log file path
    if log_file is None:
        log_file = Path(config.log_file)
        if not log_file.is_absolute():
            log_file = Path(__file__).parent.parent / log_file
    else:
        log_file = Path(log_file)

    # Set log level from config if not provided
    if log_level is None:
        log_level = config.log_level

    # Set file rotation parameters from config if not provided
    if max_bytes is None:
        max_bytes = config.log_max_bytes
    if backup_count is None:
        backup_count = config.log_backup_count

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(detailed_formatter)

    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))  # Use same level as file
    console_handler.setFormatter(simple_formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    configure_loggers()

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - File: {log_file}, Level: {log_level}")


def configure_loggers() -> None:
    """Configure specific loggers for different modules."""

    # FastAPI/Uvicorn loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # Supabase client (can be verbose)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("postgrest").setLevel(logging.WARNING)

    # HTTP client libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Agents SDK
    logging.getLogger("agents").setLevel(logging.INFO)

    # Application loggers
    logging.getLogger("src.core").setLevel(logging.DEBUG)
    logging.getLogger("src.api").setLevel(logging.DEBUG)
    logging.getLogger("src.tooling").setLevel(logging.DEBUG)
    logging.getLogger("src.chats").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
