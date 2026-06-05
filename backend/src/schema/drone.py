from uuid import UUID
from pydantic import BaseModel


class ResponseDrone(BaseModel):
    name: str
    location: UUID
    destination: UUID
