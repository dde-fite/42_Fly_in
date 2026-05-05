from __future__ import annotations
from typing import Any, TYPE_CHECKING
from enum import Enum
from pydantic import Field, field_validator, ConfigDict
from pydantic_extra_types.color import Color
from src.core.errors import TrafficError
from .transitable_zone import TransitableZone
from .vector import Vector
from .turn import Turn
from .slot_booking import SlotBooking

if TYPE_CHECKING:
    from .drone import Drone
    from .connection import Connection


class HubAccess(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


# Movement cost (in turns) to *enter* a hub, keyed by its access level.
# None means the hub is impassable.
HubCost: dict[HubAccess, int | None] = {
    HubAccess.NORMAL: 1,
    HubAccess.BLOCKED: None,
    HubAccess.RESTRICTED: 2,
    HubAccess.PRIORITY: 1,
}


class Hub(TransitableZone):
    """
    A named waypoint in the airspace graph.

    Hubs are the nodes of the graph; :class:`Connection` objects are the edges.
    Drones spawn at hubs, rest between connections, and reach their destination
    at a hub.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: str | None = None
    connections: set[Connection] = Field(default_factory=set)

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("name", mode="after")
    @classmethod
    def check_name(cls, value: str) -> str:
        if "-" in value:
            raise ValueError("Hub names cannot contain dashes (-)")
        return value

    @field_validator("color", mode="after")
    @classmethod
    def check_color(cls, value: str | None) -> str | None:
        if value is None or value == "rainbow":
            return value
        Color(value)
        return value

    # ------------------------------------------------------------------
    # Graph helpers
    # ------------------------------------------------------------------

    def get_connection_by_hub(self, hub: Hub) -> Connection | None:
        """Return the Connection linking this hub to *hub*, or None."""
        for c in self.connections:
            if hub in c.hubs:
                return c
        return None

    def is_reachable(self) -> bool:
        """Return True unless this hub is blocked."""
        return self.access != HubAccess.BLOCKED

    # ------------------------------------------------------------------
    # TransitableZone interface
    # ------------------------------------------------------------------

    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        """Hubs always cost 1 turn to pass through (unless blocked)."""
        return 0

    def get_next_available_entry(self, from_turn: Turn, destination: Hub | None = None) -> Turn:
        """Return the earliest turn >= *from_turn* where a slot is free."""
        i = Turn(from_turn.value)
        while self.get_occupancy(i) >= self.capacity:
            i.value += 1
        return i

    def get_next_available_exit(self, from_turn: Turn, destination: Hub) -> Turn:
        """
        Return the earliest turn at which a drone can leave this hub toward
        *destination*, factoring in the connection's availability.
        """
        connection = self.get_connection_by_hub(destination)
        if connection is None:
            raise TrafficError(
                f"No connection between hub '{self.name}' and '{destination.name}'"
            )
        return connection.get_next_available_entry(from_turn, destination)

    def accept_drone_spawn(self, drone: Drone) -> None:
        """
        Place a freshly created drone at this hub.

        Unlike ``accept_from_colateral`` this does not require a pre-existing
        booking; instead it creates an open-ended booking for the spawn turn.
        """
        if drone in self.drones:
            raise TrafficError("Drone is already in this hub")
        if len(self.drones) + 1 > self.capacity:
            raise TrafficError("Hub capacity exceeded on spawn")

        # # Create an open-ended booking so the itinerary can later add an exit.
        # spawn_booking = SlotBooking(
        #     host=self,
        #     guest=drone,
        #     enter_turn=drone.turn,
        #     exit_turn=None,
        # )
        # self._bookings.append(spawn_booking)
        self.drones.add(drone)

    def request_exit(self, drone: Drone) -> None:
        """
        Attempt to move *drone* out of this hub into the next zone on its
        itinerary.
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
    # Dunder helpers
    # ------------------------------------------------------------------

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Hub):
            return NotImplemented
        return self.name == other.name

    def __repr__(self) -> str:
        return f"Hub(name={self.name!r}, access={self.access.value})"
