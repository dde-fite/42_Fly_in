from typing import Any
from fastapi import UploadFile
from pydantic_extra_types import Color
from src.models import Simulation, Hub, HubType, Connection, Vector, Drone
from src.core.logging import logger


def parse_params(raw_params: str) -> dict[str, Any]:
    params: dict[str, Any] = dict()
    raw_params = raw_params.strip()
    if raw_params[0] != "[" or raw_params[-1] != "]":
        raise ValueError("Params contains sintax errors")
    raw_params = raw_params.removeprefix("[").removesuffix("]")
    for arg in raw_params.split():
        value: Any
        key, value = arg.split("=", 1)
        key, value = key.strip(), value.strip()
        if value.isdigit():
            value = int(value)
        params[key] = value
    return params


def parse_hub(raw: str, type: HubType = HubType.INTERMEDIATE) -> Hub:
    splits = raw.split(maxsplit=3)
    name = splits[0].strip()
    pos = Vector(x=int(splits[1]), y=int(splits[2]))
    params: dict[str, Any] = dict()
    if len(splits) == 4:
        for key, value in parse_params(splits[3]).items():
            match key:
                case "zone":
                    params["access"] = value
                case "color":
                    params["color"] = Color(value)
                case "max_drones":
                    params["capacity"] = int(value)
                case _:
                    pass
    return (Hub(name=name, position=pos, hub_type=type, **params))


def parse_connection(raw: str, hubs: list[Hub]) -> Connection:
    splits = raw.split(maxsplit=2)
    p1, p2 = splits[0].split("-")
    p1 = next(filter(lambda x: x.name == p1, hubs))
    p2 = next(filter(lambda x: x.name == p2, hubs))
    params: dict[str, Any] = dict()
    if len(splits) == 3:
        for key, value in parse_params(splits[2]).items():
            match key:
                case "max_link_capacity":
                    params["capacity"] = value
                case _:
                    pass
    return (Connection(hubs=(p1, p2), **params))


async def parse_map(file: UploadFile) -> Simulation:
    nb_drones: int | None = None
    hubs: list[Hub] = []
    connection: list[Connection] = []
    drones: list[Drone] = []
    content = await file.read()
    text = content.decode()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if len(line) < 1:
            continue
        splits = line.split(":", 1)
        if len(splits) < 2:
            raise ValueError("Map contains sintax errors")
        key, value = splits
        match key.strip():
            case "nb_drones":
                if nb_drones:
                    raise ValueError(
                        "nb_drones can not be declared more than 1 time"
                    )
                nb_drones = int(value)
            case "start_hub":
                hubs.append(parse_hub(value, type=HubType.ORIGIN))
            case "end_hub":
                hubs.append(parse_hub(value, type=HubType.DESTINATION))
            case "hub":
                hubs.append(parse_hub(value, type=HubType.INTERMEDIATE))
            case "connection":
                connection.append(parse_connection(value, hubs))
            case _:
                raise ValueError(f"Type {key} not recognized")
    if nb_drones and nb_drones > 0:
        for _d in range(nb_drones):
            drones.append(
                Drone(
                    hub=next(filter(
                        lambda x: x.hub_type == HubType.ORIGIN, hubs)
                        )
                )
            )
    logger.debug(f"Loaded map with {nb_drones} drones")
    return Simulation(hubs=hubs, connection=connection, drones=drones)
