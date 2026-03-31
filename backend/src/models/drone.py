from pydantic import BaseModel
from .hub import Hub


class Drone(BaseModel):
    hub: Hub
    in_transit_to: Hub | None = None
