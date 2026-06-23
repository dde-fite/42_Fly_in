from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from src.core import TrafficError, logger
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
        """Register this connection with both endpoint hubs after init."""
        for hub in self.hubs:
            hub.connections.add(self)

    # ------------------------------------------------------------------
    # TransitableZone interface
    # ------------------------------------------------------------------

    def get_collaterals(self) -> list[TransitableZone]:
        """Return both endpoint hubs as collateral zones."""
        return list(self.hubs)

    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        """
        Return the cost (in turns) to traverse this connection toward
        *direction*.  If *direction* is None the cost is undefined (None).
        """
        if direction is None:
            return None
        hub_cost = HubCost[direction.access]
        if hub_cost is None:
            return None
        origin_cost = self.other_hub(direction).get_movement_cost()
        if origin_cost is None:
            origin_cost = 0
        return max(0, hub_cost - origin_cost)

    def get_next_available_entry(
        self,
        from_turn: Turn,
        destination: TransitableZone | None = None
    ) -> Turn | None:
        """
        Return the earliest turn >= *from_turn* where a slot is free.

        Args:
            from_turn (Turn): Earliest candidate entry turn.
            destination (TransitableZone | None): The hub this connection
                leads toward; required to compute movement cost and verify
                the destination has an open slot upon arrival.

        Returns:
            Turn | None: Earliest available entry turn, or None if the
                destination is unreachable or the connection is mixed
                (some bookings without exit turns).

        Raises:
            TrafficError: If *destination* is not provided.
        """
        if not destination:
            raise TrafficError(
                "A destination is required to calculate entry turn"
            )
        if not isinstance(destination, Hub):
            raise TrafficError(
                "Connection destination must be a Hub"
            )
        mov_cost = self.get_movement_cost(destination)
        if mov_cost is None:
            return None
        i = Turn(from_turn.value)
        has_exits = [False if slot.exit_turn is None else True
                     for slot in self._bookings]
        if has_exits and not all(has_exits):
            return None
        _MAX_SEARCH = 1000
        for _ in range(_MAX_SEARCH):
            full = self.get_occupancy(i) >= self.capacity
            dest_entry = destination.get_next_available_entry(
                Turn(i.value + mov_cost)
            )
            if not dest_entry:
                i = Turn(i.value + 1)
                continue
            dest_blocked = dest_entry.value != i.value + mov_cost
            if not full and not dest_blocked:
                return i
            i = Turn(i.value + 1)
        return None

    def get_next_available_exit(
        self,
        from_turn: Turn,
        destination: Hub
    ) -> Turn | None:
        """
        Return the earliest turn at which a drone can exit this connection
        into *destination*.
        """
        if destination not in self.hubs:
            raise TrafficError(
                f"Hub '{destination.name}' is not an endpoint of this "
                "connection"
            )
        mov_cost = self.get_movement_cost(destination)
        if mov_cost is None:
            return None
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
            logger.debug(f"[CONNECTION {self}] Requesting exit for drone "
                         f"{drone} at collateral zone '{next_booking.host}'")
            next_booking.host.accept_from_collateral(drone)
        except TrafficError:
            logger.debug(f"[CONNECTION {self}] Denied exit for drone {drone}")
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

    def __str__(self) -> str:
        names = "<->".join(h.name for h in self.hubs)
        return names
