from pydantic import BaseModel, Field
from .hub import Hub


class Connection(BaseModel):
    hubs: tuple[Hub, Hub]
    capacity: int = Field(ge=1, default=1)
