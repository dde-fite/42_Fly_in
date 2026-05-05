from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from src.core.errors import TrafficError
from .transitable_zone import TransitableZone
from .turn import Turn
from .hub import Hub, HubCost

if TYPE_CHECKING:
    from .drone import Drone


class Connection(TransitableZone):
    """
    A directed edge between exactly two :class:`Hub` instances.

    The movement cost to traverse a connection is determined by the access
    level of the destination hub (the hub a drone is heading toward).
    """

    hubs: frozenset[Hub] = Field(min_length=2, max_length=2)

    def model_post_init(self, context: Any) -> None:
        # Register this connection with both endpoint hubs.
        for hub in self.hubs:
            hub.connections.add(self)

    # ------------------------------------------------------------------
    # TransitableZone interface
    # ------------------------------------------------------------------

    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        """
        Return the cost (in turns) to traverse this connection toward
        *direction*.  If *direction* is None the cost is undefined (None).
        """
        if direction is None:
            return None
        return HubCost[direction.access]

    def get_next_available_entry(self, from_turn: Turn, destination: Hub | None = None) -> Turn:
        """Return the earliest turn >= *from_turn* where a slot is free."""
        if not destination:
            raise TrafficError("It is required destination for calculate enty")
        mov_cost = self.get_movement_cost(destination)
        if mov_cost is None:
            raise TrafficError(
                f"Hub '{destination.name}' does not accepts arrivals"
            )
        i = Turn(from_turn.value)
        while True:
            full = self.get_occupancy(i) >= self.capacity
            dest_blocked = destination.get_next_available_entry(
                Turn(i.value + mov_cost)
            ).value != i.value + mov_cost
            if not full and not dest_blocked:
                break
            i = Turn(i.value + 1)
        return i

    def get_next_available_exit(self, from_turn: Turn, destination: Hub) -> Turn:
        """
        Return the earliest turn at which a drone can exit this connection
        into *destination*.
        """
        if destination not in self.hubs:
            raise TrafficError(
                f"Hub '{destination.name}' is not an endpoint of this connection"
            )
        mov_cost = self.get_movement_cost(destination)
        if not mov_cost:
            raise TrafficError(
                f"Hub '{destination.name}' does not accepts arrivals"
            )
        return Turn(from_turn.value + mov_cost)

    def request_exit(self, drone: Drone) -> None:
        """
        Attempt to move *drone* out of this connection into the next hub on
        its itinerary.
        """
        b = self.get_booking_for_drone(drone)
        if not b or not b.exit_turn:
            return
        if b.exit_turn.value > self.turn.value:
            return

        if not drone.itinerary or len(drone.itinerary.bookings) < 2:
            return

        next_booking = drone.itinerary.bookings[1]
        try:
            next_booking.host.accept_from_colateral(drone)
        except TrafficError:
            return

        self.unbook(b)
        self.drones.discard(drone)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def other_hub(self, hub: Hub) -> Hub:
        """Return the endpoint that is not *hub*."""
        for h in self.hubs:
            if h != hub:
                return h
        raise TrafficError("Hub is not an endpoint of this connection")

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __hash__(self) -> int:
        return hash(self.hubs)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Connection):
            return NotImplemented
        return self.hubs == other.hubs

    def __repr__(self) -> str:
        names = " <-> ".join(h.name for h in self.hubs)
        return f"Connection({names})"
