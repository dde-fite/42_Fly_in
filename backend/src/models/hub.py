from typing import Any
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from pydantic_extra_types import Color
from .vector import Vector
from ..schema.references import HubRef, DroneRef, ConnectionRef, Turn
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


class Hub(BaseModel):
    id: HubRef = Field(default_factory=lambda: HubRef(uuid4()))
    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: Color | None = None
    drones: set[DroneRef] = set()
    capacity: int = Field(ge=1, default=1)
    connections: set[Connection] = set()

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str) -> str:
        if "-" in value:
            raise ValueError("Hub names can not contain dashes(-)")
        return value

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.__arrivals: dict[int, list[DroneRef]] = {}
        self.__departures: dict[int, list[DroneRef]] = {}

    def available_at(self, turn: Turn) -> bool:
        pass

    def get_occupancy(self, turn: int) -> list[DroneRef]:
        occ: list[DroneRef] = []
        for i in range(turn + 1):
            occ.extend(self.__arrivals.get(i, []))
            for drone in self.__departures.get(i, []):
                if drone in occ:
                    occ.remove(drone)
        return occ


    def __hash__(self) -> int:
        return hash(self.id)
