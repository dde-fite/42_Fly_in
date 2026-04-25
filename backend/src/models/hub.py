from __future__ import annotations
from typing import Any, TYPE_CHECKING
from enum import Enum
from uuid import uuid4
from pydantic import Field, field_validator
from pydantic_extra_types import Color
from src.schema.references import HubRef
from .transitable_zone import TransitableZone
from .vector import Vector

if TYPE_CHECKING:
    from .connection import Connection


class HubAccess(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


HubCost: dict[HubAccess, int | None] = {
    HubAccess.NORMAL: 1,
    HubAccess.BLOCKED: None,
    HubAccess.RESTRICTED: 2,
    HubAccess.PRIORITY: 1
}


class Hub(TransitableZone):
    id: HubRef = Field(default_factory=lambda: HubRef(uuid4()))
    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: str | None = None
    connections: set[Connection] = set()

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str) -> str:
        if "-" in value:
            raise ValueError("Hub names can not contain dashes(-)")
        return value

    @field_validator('color', mode='after')
    @classmethod
    def check_color(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value == "rainbow":
            return value
        Color(value)
        return value

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Hub):
            return False
        return hash(self.name) == hash(other.name)
