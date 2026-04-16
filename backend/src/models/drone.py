from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import uuid4
from pydantic import BaseModel, Field
from src.schema.references import DroneRef
from .trajectory import Trajectory
from .turn import Turn

if TYPE_CHECKING:
    from .connection import Connection
    from .hub import Hub


class Transit(BaseModel):
    destination: Hub
    turns_elapsed: Turn = Turn(0)


class Drone(BaseModel):
    id: DroneRef = Field(default_factory=lambda: DroneRef(uuid4()))
    location: Hub | Connection
    in_transit_to: Transit | None = None
    trajectory: Trajectory | None = None

    def __hash__(self) -> int:
        return hash(self.id)
