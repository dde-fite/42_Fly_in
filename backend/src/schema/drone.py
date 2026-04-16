from pydantic import BaseModel
from .references import HubRef, ConnectionRef


class ResponseTransit(BaseModel):
    destination: HubRef
    turns_elapsed: int


class ResponseDrone(BaseModel):
    location: HubRef | ConnectionRef
    in_transit_to: ResponseTransit | None = None
