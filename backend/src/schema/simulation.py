from pydantic import BaseModel
from .references import HubRef, ConnectionRef, DroneRef


class ResponseSimulation(BaseModel):
    turns: int
    hubs: list[HubRef]
    origin: HubRef
    destination: HubRef
    connections: list[ConnectionRef]
    drones: list[DroneRef]
