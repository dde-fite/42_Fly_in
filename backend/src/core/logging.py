import logging
from .config import config

logger = logging.getLogger('uvicorn.error')


def setup_logging() -> None:
    logger.setLevel(config.LOG_LEVEL)
