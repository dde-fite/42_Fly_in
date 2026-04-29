from uuid import UUID
from pydantic import BaseModel


class ResponseDrone(BaseModel):
    location: UUID
    destination: UUID
