import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.settings.config import LOG_FILE_PATH

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_LOG_SIZE = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
_IS_CONFIGURED = False


def configure_logging(level: Optional[int] = None) -> logging.Logger:
    """Configure root logging with a RotatingFileHandler and console handler."""
    global _IS_CONFIGURED

    if _IS_CONFIGURED:
        return logging.getLogger()

    resolved_level = level or getattr(logging, DEFAULT_LEVEL, logging.INFO)
    log_dir = os.path.dirname(LOG_FILE_PATH)
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(resolved_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(resolved_level)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(resolved_level)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    _IS_CONFIGURED = True
    return logger
