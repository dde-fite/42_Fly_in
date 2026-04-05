from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic_extra_types import Color
from .vector import Vector


class HubAccess(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Hub(BaseModel):
    name: str
    position: Vector
    access: HubAccess = HubAccess.NORMAL
    color: Color | None = None
    capacity: int = Field(ge=1, default=1)

    @field_validator('name', mode='after')
    @classmethod
    def check_name(cls, value: str) -> str:
        if "-" in value:
            raise ValueError("Hub names can not contain dashes(-)")
        return value

    def __hash__(self) -> int:
        return hash(self.name)
