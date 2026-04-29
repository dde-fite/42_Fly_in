from uuid import UUID
from pydantic import BaseModel, Field


class ResponseConnection(BaseModel):
    hubs: list[UUID] = Field(min_length=2, max_length=2)
    capacity: int = Field(ge=1, default=1)
