from uuid import UUID
from pydantic import BaseModel


class ResponseDrone(BaseModel):
    name: str
    location: UUID
    destination: UUID
    # Id of the drone's active itinerary (None when unrouted or arrived). Look
    # it up via GET /itineraries for the full route and slot schedule.
    itinerary: UUID | None = None
