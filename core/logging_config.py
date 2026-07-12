#!/usr/bin/env python3
"""
Structured logging configuration for WowFactor.

Provides setup_logging() which configures a rotating file handler and a
console handler on stderr, all using a consistent log format.

Typical usage::

    from core.logging_config import setup_logging
    setup_logging(level="INFO")
"""

import logging
import logging.handlers
import os
from typing import Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = "logs"
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "wowfactor.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5              # keep 5 rotated files
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"


def setup_logging(
    level: Union[int, str] = "INFO",
    log_file: str = DEFAULT_LOG_FILE,
) -> logging.Logger:
    """Configure the root logger for the application.

    Creates a RotatingFileHandler (10 MB / 5 backups) and a StreamHandler
    writing to stderr, both using the standard ``LOG_FORMAT``.

    Args:
        level:    Logging level (e.g. ``"DEBUG"``, ``logging.INFO``, 20).
        log_file: Path to the log file.  The containing directory is created
                  automatically if it does not exist.

    Returns:
        The root ``logging.Logger`` instance (already configured).
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()

    root.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(stream=None)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("psutil").setLevel(logging.WARNING)

    return root