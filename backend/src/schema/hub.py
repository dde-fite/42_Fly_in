from pydantic import BaseModel, Field
from .references import DroneRef, ConnectionRef


class ResponseHub(BaseModel):
    name: str
    position: tuple[int, int]
    access: str
    color: str | None = None
    drones: list[DroneRef] = []
    capacity: int = Field(ge=1, default=1)
    connections: list[ConnectionRef] = []
