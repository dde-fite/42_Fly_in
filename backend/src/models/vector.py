from pydantic import BaseModel, Field


class Vector(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
