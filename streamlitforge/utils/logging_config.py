"""Logging configuration for StreamlitForge."""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str = None):
    """Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Example:
        >>> setup_logging(level="DEBUG")
        >>> setup_logging(level="INFO", log_file="app.log")
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatters
    console_formatter = logging.Formatter(log_format)

    # Create handlers
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(console_formatter)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers = []  # Clear any existing handlers

    for handler in handlers:
        handler.setFormatter(console_formatter)
        root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    third_party_loggers = [
        "urllib3",
        "requests",
        "httpx",
        "httpcore",
        "httpclient",
        "openai",
        "tiktoken",
    ]

    for logger_name in third_party_loggers:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
    """
    return logging.getLogger(name)
