from uuid import uuid4
from pydantic import BaseModel, Field
from ..schema.references import HubRef, ConnectionRef, DroneRef
from .trajectory import Trajectory

if T


class Transit(BaseModel):
    destination: HubRef
    turns_elapsed: int = 0


class Drone(BaseModel):
    id: DroneRef = Field(default_factory=lambda: DroneRef(uuid4()))
    location: HubRef | ConnectionRef
    in_transit_to: Transit | None = None
    trajectory: Trajectory | None = None

    def __hash__(self) -> int:
        return hash(self.id)
