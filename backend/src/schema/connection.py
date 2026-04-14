from pydantic import BaseModel, Field
from src.schema import HubRef


class ResponseConnection(BaseModel):
    hubs: list[HubRef] = Field(min_length=2, max_length=2)
    capacity: int = Field(ge=1, default=1)
