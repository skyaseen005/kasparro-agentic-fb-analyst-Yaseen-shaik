"""
Logging utilities for the agentic system
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger


def setup_logger():
    """
    Setup loguru logger with:
      - Console readable output (colored)
      - JSON structured file logs (serialize=True)
      - Plain text readable file logs
    All file outputs use utf-8 encoding to avoid Windows chardef issues.
    """
    # ensure logs dir exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # remove default handlers
    logger.remove()

    # Console logger — pretty + color
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,  # thread/process safe
        backtrace=True,
        diagnose=False,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON Structured Log file (Loguru handles serialization)
    json_log_path = log_dir / f"run_{timestamp}.json"
    logger.add(
        str(json_log_path),
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        serialize=True,      # writes proper JSON objects per line
        encoding="utf-8",
        enqueue=True,
    )

    # Plain text readable file
    text_log_path = log_dir / f"run_{timestamp}.log"
    logger.add(
        str(text_log_path),
        level="DEBUG",
        rotation="10 MB",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
        encoding="utf-8",
        enqueue=True,
    )

    logger.info(f"Logger initialized. Logs: {json_log_path}")
    return logger


def get_logger(name: str):
    """Return namespaced logger instance"""
    return logger.bind(name=name)
