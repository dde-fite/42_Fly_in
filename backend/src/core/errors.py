from .logging import logger


class ParseError(Exception):
    """Raised when the map file contains a syntax or semantic error."""

    def __init__(self, msg: str, line: str | None = None) -> None:
        """
        Initialize ParseError with a message and the offending line.

        Args:
            msg (str): Human-readable description of the error.
            line (str | None): The raw map line that caused the error,
                or None if the error is not line-specific.
        """
        self.msg = msg
        self.line = line
        logger.debug("%s line=%s", msg, line)


class SimulationAlreadyAllocated(Exception):
    """Raised when a token already has a simulation registered."""

    def __init__(self, *args: object) -> None:
        """Initialize and log the error."""
        super().__init__(*args)
        logger.debug(*args if args else ("SimulationAlreadyAllocated",))


class SimulationNotFound(Exception):
    """Raised when no simulation is found for the given token."""

    def __init__(self, *args: object) -> None:
        """Initialize and log the error."""
        super().__init__(*args)
        logger.debug(*args)


class KeyExpiredError(KeyError):
    """Raised when a cache key has expired."""

    def __init__(self, *args: object) -> None:
        """Initialize and log the error."""
        super().__init__(*args)
        logger.debug(*args)


class ZoneNotAvailable(Exception):
    """Raised when a drone cannot be booked into a zone due to capacity."""


class TrafficError(Exception):
    """Raised for logical errors in drone routing or zone management."""


class ExpiredItinerary(Exception):
    """Raised when a drone's itinerary becomes stale and must be destroyed."""


class SimulationConflict(Exception):
    """Raised when a simulation operation violates structural constraints."""
