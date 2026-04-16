from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel
from .turn import Turn

if TYPE_CHECKING:
    from .hub import Hub
    from .drone import Drone
    from .connection import Connection


class Simulation(BaseModel):
    turns: Turn = Turn(0)
    hubs: set[Hub]
    origin: Hub
    destination: Hub
    connections: set[Connection]
    drones: set[Drone]
