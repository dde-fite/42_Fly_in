from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field, model_validator
from src.core.errors import TrafficError
from .transitable_zone import TransitableZone
from .turn import Turn

if TYPE_CHECKING:
    from .hub import Hub, HubCost
    from .drone import Drone


class Connection(TransitableZone):
    hubs: frozenset[Hub] = Field(min_length=2, max_length=2)

    def model_post_init(self, context: Any) -> None:
        for hub in self.hubs:
            hub.connections.add(self)

    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        if not direction:
            return None
        return HubCost[direction.access]

    def get_next_available_exit(self, from_turn: Turn, destination: "Hub") -> Turn:
        if destination not in self.hubs:
            raise TrafficError(
                f"Hub '{destination.name}' is not connected to this connection"
            )
        return destination.get_next_available_entry(from_turn)

    def request_exit(self, drone: Drone) -> None:
        b = self.get_booking_for_drone(drone)
        if (not b or not b.exit_turn or
           not b.exit_turn.value >= self.turn.value):
            return
        next_hub = drone.itinerary.bookings[1]
        try:
            next_hub.host.accept_from_colateral(drone)
        except TrafficError:
            return
        self.unbook(b)
        self.drones.remove(drone)

    def __hash__(self) -> int:
        return hash(self.hubs)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Connection):
            return False
        return hash(self.hubs) == hash(other.hubs)
