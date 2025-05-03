"""
Logging utilities for configuring application logging.
"""
import os
import logging
import logging.handlers
from datetime import datetime

import app.config as config


def setup_logger(log_level=None, log_file=None, console=True):
    """
    Configure application logging.

    Args:
        log_level (int, optional): Logging level. Defaults to config.LOG_LEVEL.
        log_file (str, optional): Path to the log file. Defaults to config.LOG_FILE.
        console (bool, optional): Whether to log to console. Defaults to True.

    Returns:
        logging.Logger: Configured root logger
    """
    # If log level not provided, use from config
    if log_level is None:
        log_level = getattr(logging, config.LOG_LEVEL)

    # If the log file not provided, use from config
    if log_file is None:
        log_file = config.LOG_FILE

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Define formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Clear existing handlers
    root_logger.handlers = []

    # Add console handler if required
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if the log file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add timestamp to log
    root_logger.info(f"Logging initialized at {datetime.now().isoformat()}")

    return root_logger


def get_module_logger(module_name):
    """
    Get a logger for a specific module.

    Args:
        module_name (str): Name of the module

    Returns:
        logging.Logger: Logger for the module
    """
    return logging.getLogger(module_name)


class LoggerMixin:
    """Mixin to add logging capability to a class."""

    @property
    def logger(self):
        """Get a logger for the class."""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


# Initialize logger when module is imported
logger = get_module_logger(__name__)
