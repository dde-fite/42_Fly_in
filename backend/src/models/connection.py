from pydantic import BaseModel, Field
from .hub import Hub


class Connection(BaseModel):
    hubs: frozenset[Hub] = Field(min_length=2, max_length=2)
    capacity: int = Field(ge=1, default=1)
