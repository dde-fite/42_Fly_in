from typing import TypedDict
from src.models import Vector


class ParsedHub(TypedDict):
    name: str
    position: Vector
    access: str
    color: str | None
    capacity: int | None
    is_origin: bool
    is_destination: bool


class ParsedConnection(TypedDict):
    hubs: list[str]
    capacity: int | None


class ParsedMap(TypedDict):
    nb_drones: int | None
    hubs: list[ParsedHub]
    connection: list[ParsedConnection]
