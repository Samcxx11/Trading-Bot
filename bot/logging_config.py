"""
Logging configuration for the trading bot.

Sets up dual logging:
  - Console handler: INFO-level, concise format for user feedback
  - File handler: DEBUG-level, detailed format for audit/debugging
"""

import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        log_dir: Directory to store log files. Created if it doesn't exist.

    Returns:
        Configured logger instance for the trading bot.
    """
    os.makedirs(log_dir, exist_ok=True)

    # Generate a timestamped log filename for each session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"trading_bot_{timestamp}.log")

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    # --- File handler: captures everything (DEBUG+) ---
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # --- Console handler: user-facing output (INFO+) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging initialized — file: %s", log_file)
    return logger
