from uuid import UUID
from pydantic import BaseModel


class ResponseSlot(BaseModel):
    zone: UUID
    enter_turn: int
    exit_turn: int | None


class ResponseItinerary(BaseModel):
    id: UUID
    drone: UUID
    slots: list[ResponseSlot]
