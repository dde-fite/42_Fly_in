from logging import (  # noqa: F401
    getLogger, CRITICAL, FATAL,
    ERROR, WARNING, WARN, INFO,
    DEBUG, NOTSET
)
from .config import config

logger = getLogger('uvicorn.error')


def setup_logging() -> None:
    """Configure the root logger level from the application config."""
    logger.setLevel(config.LOG_LEVEL)
