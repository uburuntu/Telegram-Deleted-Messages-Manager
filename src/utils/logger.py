"""
Logging utility for the application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "telegram_manager",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    verbose: bool = False,
) -> logging.Logger:
    """
    Set up application logger with console and optional file output.

    Args:
        name: Logger name
        level: Base logging level
        log_file: Optional file path for logging
        verbose: Enable verbose (DEBUG) logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level based on verbose flag
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Format: [2025-01-01 12:00:00] INFO: Message
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "telegram_manager") -> logging.Logger:
    """
    Get existing logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Check if running in development mode
def is_dev_mode() -> bool:
    """Check if running in development mode."""
    return not getattr(sys, "frozen", False)


# Default logger with verbose mode for development
_verbose = is_dev_mode()
default_logger = setup_logger(verbose=_verbose)
