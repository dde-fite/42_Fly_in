from pydantic import BaseModel
from .turn import Turn
from .hub import Hub
from .drone import Drone
from .connection import Connection


class Simulation(BaseModel):
    turn: Turn
    hubs: set[Hub]
    origin: Hub
    destination: Hub
    connections: set[Connection]
    drones: set[Drone]
