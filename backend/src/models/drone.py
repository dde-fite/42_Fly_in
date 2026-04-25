from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import uuid4
from pydantic import BaseModel, Field
from src.schema.references import DroneRef
from src.core.errors import TrafficError
from .turn import Turn
from .itinerary import Itinerary

if TYPE_CHECKING:
    from .transitable_zone import TransitableZone


class Drone(BaseModel):
    id: DroneRef = Field(default_factory=lambda: DroneRef(uuid4()))
    destination: TransitableZone
    itinerary: Itinerary | None = None
    turn: Turn
    _location: TransitableZone

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
        if bookings[0].host != self.location:
            raise TrafficError(
                "Drone does not have permission to stay in current location"
            )
        if bookings[0].exit_turn is None:
            # ask TrafficController an itinerary
            # if no one returned, not move
            return
        if bookings[0].exit_turn.value > self.turn.value:
            self.location.request_exit(self)

    def __hash__(self) -> int:
        return hash(self.id)
