from __future__ import annotations
from typing import Any, TYPE_CHECKING
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from pydantic_extra_types import Color
from src.schema.references import HubRef

if TYPE_CHECKING:
    from .connection import Connection
    from .drone import Drone
    from .vector import Vector


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


class Hub(BaseModel):
    id: HubRef = Field(default_factory=lambda: HubRef(uuid4()))
    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: str | None = None
    drones: set[Drone] = set()
    capacity: int = Field(ge=1, default=1)
    capacity_defined: bool = False
    connections: set[Connection] = set()
    _arrivals: dict[int, list[Drone]] = {}
    _departures: dict[int, list[Drone]] = {}

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

    # def available_at(self, turn: Turn) -> bool:
    #     pass

    # def get_occupancy(self, turn: int) -> list[Drone]:
    #     occ: list[DroneRef] = []
    #     for i in range(turn + 1):
    #         occ.extend(self.__arrivals.get(i, []))
    #         for drone in self.__departures.get(i, []):
    #             if drone in occ:
    #                 occ.remove(drone)
    #     return occ

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any):
        if not isinstance(other, Hub):
            return False
        return hash(self.name) == hash(other.name)
