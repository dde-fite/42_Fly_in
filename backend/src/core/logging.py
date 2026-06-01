from logging import (getLogger, CRITICAL, FATAL,
                     ERROR, WARNING, WARN, INFO,
                     DEBUG, NOTSET)
from .config import config

logger = getLogger('uvicorn.error')


def setup_logging() -> None:
    logger.setLevel(config.LOG_LEVEL)
