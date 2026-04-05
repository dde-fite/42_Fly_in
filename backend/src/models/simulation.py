from pydantic import BaseModel
from .hub import Hub
from .drone import Drone
from .connection import Connection


class Simulation(BaseModel):
    turns: int = 0
    hubs: list[Hub]
    origin: Hub
    destination: Hub
    connections: list[Connection]
    drones: list[Drone]


class SimulationWithToken(BaseModel):
    token: str
    simulation: Simulation
