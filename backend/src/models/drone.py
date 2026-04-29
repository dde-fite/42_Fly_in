from __future__ import annotations
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, model_validator, PrivateAttr
from src.core.errors import TrafficError
from .turn import Turn

if TYPE_CHECKING:
    from .transitable_zone import TransitableZone
    from .itinerary import Itinerary
    from .hub import Hub


class Drone(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID = Field(default_factory=lambda: uuid4())
    origin: Hub
    destination: Hub
    turn: Turn
    itinerary: Itinerary | None = None
    _location: TransitableZone = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        self.origin.accept_drone_spawn(self)
        self._location = self.origin

    @property
    def location(self) -> TransitableZone:
        return self._location

    @location.setter
    def location(self, zone: TransitableZone) -> None:
        if not self.itinerary:
            raise TrafficError("Drone needs an itinerary to move")
        if zone != self.itinerary.bookings[1].host:
            raise TrafficError(
                "Drone does not have permission to move to that zone"
            )
        self._location = zone
        self.itinerary.pop_booking()

    def tick(self) -> None:
        if self.location == self.destination:
            return
        if not self.itinerary:
            # ask TrafficController an itinerary
            # if no one returned, not move
            return
        bookings = self.itinerary.bookings
        if bookings[0].exit_turn is None:
            # ask TrafficController an itinerary
            # if no one returned, not move
            return
        if bookings[0].exit_turn.value > self.turn.value:
            self.location.request_exit(self)

    def __hash__(self) -> int:
        return hash(self.id)
