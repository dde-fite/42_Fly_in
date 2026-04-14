from pydantic import BaseModel, Field
from src.models import Vector, HubAccess
from src.schema import DroneRef, ConnectionRef


class ResponseHub(BaseModel):
    name: str
    position: Vector
    access: HubAccess
    color: str | None = None
    drones: list[DroneRef] = []
    capacity: int = Field(ge=1, default=1)
    connections: list[ConnectionRef] = []
