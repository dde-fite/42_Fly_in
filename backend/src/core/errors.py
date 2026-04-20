from .logging import logger


class ParseError(Exception):
    def __init__(self, msg: str, line: str | None = None):
        self.msg = msg
        self.line = line
        logger.debug("%s line=%s", msg, line)


class SimulationAlreadyAllocated(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.debug(*args)


class SimulationNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.debug(*args)


class KeyExpiredError(KeyError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.debug(*args)
