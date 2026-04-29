from uuid import UUID
from pydantic import BaseModel


class ResponseSimulation(BaseModel):
    turn: int
    hubs: list[UUID]
    origin: UUID
    destination: UUID
    connections: list[UUID]
    drones: list[UUID]
