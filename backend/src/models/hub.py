from __future__ import annotations
from typing import Any
from enum import Enum
from pydantic import Field, field_validator, ConfigDict
from pydantic_extra_types import Color
from src.core.errors import TrafficError
from .transitable_zone import TransitableZone
from .vector import Vector
from .drone import Drone
from .turn import Turn
from .connection import Connection


class HubAccess(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


HubCost: dict[HubAccess, int | None] = {
    HubAccess.NORMAL: 1,
    HubAccess.BLOCKED: None,
    HubAccess.RESTRICTED: 2,
    HubAccess.PRIORITY: 1
}


class Hub(TransitableZone):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: str | None = None
    connections: set[Connection] = Field(default_factory=set[Connection])

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str) -> str:
        if "-" in value:
            raise ValueError("Hub names can not contain dashes(-)")
        return value

    @field_validator('color', mode='after')
    @classmethod
    def check_color(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value == "rainbow":
            return value
        Color(value)
        return value

    def get_connection_by_hub(self, hub: Hub) -> Connection | None:
        for c in self.connections:
            if hub in c.hubs:
                return c
        return None

    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        return 1

    def get_next_available_exit(self, from_turn: Turn, destination: "Hub") -> Turn:
        connection = next(
            (c for c in self.connections if destination in c.hubs),
            None
        )
        if connection is None:
            raise TrafficError(
                f"No connection between hub '{self.name}' and '{destination.name}'"
            )
        turn = connection.get_next_available_entry(from_turn)
        turn = connection.get_next_available_exit(turn, destination)
        return turn

    def accept_drone_spawn(self, drone: Drone) -> None:
        if drone in self.drones:
            raise TrafficError("Drone is already in the hub")
        if len(self.drones) + 1 > self.capacity:
            raise TrafficError("Hub capacity exceeded on spawn")
        self.drones.add(drone)

    def request_exit(self, drone: Drone) -> None:
        b = self.get_booking_for_drone(drone)
        if (not b or not b.exit_turn or
           not b.exit_turn.value >= self.turn.value):
            return
        con = drone.itinerary.bookings[1]
        try:
            con.host.accept_from_colateral(drone)
        except TrafficError:
            return
        self.unbook(b)
        self.drones.remove(drone)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Hub):
            return False
        return hash(self.name) == hash(other.name)
