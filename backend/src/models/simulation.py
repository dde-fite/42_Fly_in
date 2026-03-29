from pydantic import BaseModel
from .hub import Hub
from .drone import Drone


class Simulation(BaseModel):
    token: str
    hubs: list[Hub]
    drones: list[Drone]
