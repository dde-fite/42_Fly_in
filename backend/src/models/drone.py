from __future__ import annotations
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from src.core import TrafficError, logger
from src.utils.ft import short_id
from .turn import Turn

if TYPE_CHECKING:
    from .transitable_zone import TransitableZone
    from .itinerary import Itinerary
    from .hub import Hub


class Drone(BaseModel):
    """
    A drone is spawned at *origin* and attempts to reach *destination*.
    Movement is governed by an :class:`Itinerary` that reserves time-slots
    in each zone along the route. On every simulation tick the drone checks
    whether it is time to move into the next zone and, if so, triggers a
    ``request_exit`` on its current location.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(default_factory=uuid4)
    origin: Hub
    destination: Hub
    turn: Turn = Turn(0)
    itinerary: Itinerary | None = None

    _location: TransitableZone = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        self.origin.accept_drone_spawn(self)
        self._location = self.origin

    # ------------------------------------------------------------------
    # Location property
    # ------------------------------------------------------------------

    @property
    def location(self) -> TransitableZone:
        return self._location

    @location.setter
    def location(self, zone: TransitableZone) -> None:
        if not self.itinerary:
            raise TrafficError("Drone needs an itinerary to move")
        # After popping the first booking the next expected zone is bookings[0].
        expected = self.itinerary.bookings[1].host if len(self.itinerary.bookings) >= 2 else None
        if zone != expected:
            raise TrafficError(
                "Drone does not have permission to move to that zone"
            )
        prev = self._location
        self._location = zone
        logger.debug(f"[DRONE {self}] Moved from '{prev}' to '{zone}'")
        self.itinerary.pop_booking()

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick(self) -> bool:
        """Advance the drone's state for the current turn."""
        if self._location == self.destination:
            return False  # Already at destination, so nothing to do.

        if not self.itinerary:
            # No itinerary yet; the TrafficController should assign one.
            return False

        if not self.itinerary.bookings:
            return False

        # Request exit when the scheduled exit turn has been reached.
        moved = False
        while True:
            actual = self.itinerary.bookings[0]
            if not actual.exit_turn:
                break
            if self.turn.value != actual.exit_turn.value:
                break
            logger.debug(f"[DRONE {self}] Requesting exit from zone"
                         f"'{self._location}'")
            self._location.request_exit(self)
            moved = True
        return moved

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Drone):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        return (
            f"Drone(id={self.id}, "
            f"origin={self.origin.name!r}, "
            f"destination={self.destination.name!r}, "
            f"turn={self.turn.value})"
        )

    def __str__(self) -> str:
        return f"D{short_id(self.id).upper()}"
