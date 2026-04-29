from uuid import UUID
from pydantic import BaseModel, Field


class ResponseHub(BaseModel):
    name: str
    position: tuple[int, int]
    access: str
    color: str | None = None
    drones: list[UUID] = []
    capacity: int = Field(ge=1, default=1)
    connections: list[UUID] = []
