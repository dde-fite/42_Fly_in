from __future__ import annotations
from typing import Any, TYPE_CHECKING
from uuid import uuid4
from pydantic import BaseModel, Field
from src.schema.references import ConnectionRef

if TYPE_CHECKING:
    from .hub import Hub


class Connection(BaseModel):
    id: ConnectionRef = Field(default_factory=lambda: ConnectionRef(uuid4()))
    hubs: frozenset[Hub] = Field(min_length=2, max_length=2)
    capacity: int = Field(ge=1, default=1)
    # _transits: dict[int, list[Drone]] = {}

    # def __init__(self, **data: Any) -> None:
    #     super().__init__(**data)

    # def get_cost(self, direction: HubRef) -> int:
    #     pass

    # def available_at(turn: Turn, direction: HubRef) -> bool:
    #     pass

    def __hash__(self) -> int:
        return hash(id)
