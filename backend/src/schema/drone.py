from pydantic import BaseModel
from .references import HubRef, ConnectionRef
from src.models import Turn


class ResponseTransit(BaseModel):
    destination: HubRef
    turns_elapsed: Turn = Turn(1)


class ResponseDrone(BaseModel):
    location: HubRef | ConnectionRef
    in_transit_to: ResponseTransit | None = None
