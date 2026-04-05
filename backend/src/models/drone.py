from pydantic import BaseModel
from .hub import Hub
from .trajectory import Trajectory


class Transit(BaseModel):
    destination: Hub
    turns_elapsed: int = 0


class Drone(BaseModel):
    hub: Hub
    in_transit_to: Transit | None = None
    trajectory: Trajectory | None = None
