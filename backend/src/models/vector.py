from dataclasses import dataclass


@dataclass(frozen=True)
class Vector:
    x: int
    y: int
