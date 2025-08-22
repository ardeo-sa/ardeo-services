"""
Logging configuration module.

This module provides a utility function `setup_logging()` to configure
the application's logging system. It sets up a JSON-formatted log file
with a configurable log level and file path.

Usage:
    from app.logging_config import setup_logging
    setup_logging()
"""
import os
import logging
from pythonjsonlogger import json

def setup_logging():
    """
        Configure the application's root logger with JSON formatting.

        Sets the log level and output file based on environment variables
        `LOG_LEVEL` and `LOG_FILE`. Existing handlers are cleared, and a
        new FileHandler with JSON formatting is added.

        Environment Variables:
            LOG_LEVEL : str
                The logging level (e.g., "DEBUG", "INFO", "WARNING").
                Defaults to "INFO" if not set.
            LOG_FILE : str
                Path to the log file. Defaults to "app.log" if not set.

        Returns:
            None
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "app.log")

    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.FileHandler(log_file)
    formatter = json.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
