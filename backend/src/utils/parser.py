from typing import Any, Iterable
from fastapi import UploadFile
from pydantic import ValidationError
from pydantic_extra_types import Color
from src.models import Simulation, Hub, Connection, Vector, Drone, Turn
from src.core import logger, ParseError
import logging


def check_hub_conflict(hub: Hub, others: Iterable[Hub], line: str) -> bool:
    if hub in others:
        raise ParseError("Duplicated hub names", line)
    for o in others:
        if o.position == hub.position:
            raise ParseError(f"Conflict with hub '{o.name}' and '{hub.name}'"
                             " coordinates", line)
    return False


def parse_params(raw_params: str) -> dict[str, Any]:
    value: Any
    params: dict[str, Any] = dict()
    raw_params = raw_params.strip()
    if not raw_params or \
       not (raw_params.startswith("[") and raw_params.endswith("]")):
        raise ParseError("Params contains sintax errors", raw_params)
    raw_params = raw_params.removeprefix("[").removesuffix("]")
    for arg in raw_params.split():
        if "=" not in arg:
            raise ParseError("Invalid param format, expected key=value", arg)
        key, value = arg.split("=", 1)
        key, value = key.strip(), value.strip()
        try:
            value = int(value)
        except ValueError:
            pass
        params[key] = value
    return params


def parse_hub(raw: str, turn: Turn) -> Hub:
    splits = raw.split(maxsplit=3)
    name = splits[0].strip()
    try:
        pos = Vector(x=int(splits[1]), y=int(splits[2]))
    except ValueError:
        raise ParseError("Hub position contains an invalid integer", raw)
    params: dict[str, Any] = dict()
    if len(splits) == 4:
        for key, value in parse_params(splits[3]).items():
            match key:
                case "zone":
                    params["access"] = value
                case "color":
                    if isinstance(value, str) and value.lower() == "rainbow":
                        params["color"] = value.lower()
                    else:
                        try:
                            params["color"] = Color(value).as_hex()
                        except ValueError:
                            raise ParseError(
                                f"Unrecognized color {value}",
                                raw
                            )
                case "max_drones":
                    params["capacity"] = value
                case _:
                    pass
    try:
        h = Hub(name=name, position=pos, **params, turn=turn)
    except ValidationError as e:
        raise ParseError(f"Error creating a hub: {e.errors(include_input=False, include_url=False)}")
    return h


def parse_connection(raw: str, hubs: set[Hub], turn: Turn) -> Connection:
    splits = raw.split(maxsplit=2)
    splits = splits[0].split("-")
    if len(splits) != 2:
        raise ParseError("Invalid connection format", raw)
    p1_name, p2_name = splits
    try:
        p1 = next(filter(lambda x: x.name == p1_name, hubs))
        p2 = next(filter(lambda x: x.name == p2_name, hubs))
    except StopIteration:
        raise ParseError(f"Unknown hub in connection: {p1_name}, {p2_name}",
                         raw)
    if p1 == p2:
        raise ParseError(f"Self connection not allowed: {p1_name}-{p2_name}",
                         raw)
    params: dict[str, Any] = dict()
    if len(splits) == 3:
        for key, value in parse_params(splits[2]).items():
            match key:
                case "max_link_capacity":
                    params["capacity"] = value
                case _:
                    pass
    try:
        con = Connection(hubs=frozenset({p1, p2}), **params, turn=turn)
    except ValidationError as e:
        raise ParseError(f"Error creating a connection: {e.errors(include_input=False, include_url=False)}")
    return con


def init_drones(nbr: int, origin: Hub, destination: Hub, turn: Turn) -> set[Drone]:
    drones: set[Drone] = set()
    for _d in range(nbr):
        try:
            d = Drone(origin=origin, destination=destination, turn=turn)
        except ValidationError as e:
            raise ParseError(f"Error creating a drone: {e.errors(include_input=False, include_url=False)}")
        except ValueError as e:
            raise ParseError(f"Error creating a drone: {e}")
        drones.add(d)
    return drones


async def parse_map(file: UploadFile) -> Simulation:
    content = await file.read()
    text = content.decode()
    turn = Turn(0)
    nb_drones: int | None = None
    hubs: set[Hub] = set()
    origin: Hub | None = None
    destination: Hub | None = None
    connection: set[Connection] = set()
    drones: set[Drone] = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if len(line) < 1:
            continue
        splits = line.split(":", 1)
        if len(splits) < 2:
            raise ParseError("Map contains sintax errors", line)
        key, value = splits
        match key.strip():
            case "nb_drones":
                if nb_drones is not None:
                    raise ParseError(
                        "Number of drones can not be declared more"
                        " than 1 time",
                        line
                    )
                value = value.strip()
                if not value.isdigit():
                    raise ParseError(
                        "Number of drones does not contains a valid"
                        " positive integer",
                        line
                    )
                nb_drones = int(value.strip())
            case "start_hub":
                if origin:
                    raise ParseError("Start hub already defined", line)
                origin = parse_hub(value, turn)
                check_hub_conflict(origin, hubs, line)
                hubs.add(origin)
            case "end_hub":
                if destination:
                    raise ParseError("Destination hub already defined", line)
                destination = parse_hub(value, turn)
                check_hub_conflict(destination, hubs, line)
                hubs.add(destination)
            case "hub":
                h = parse_hub(value, turn)
                check_hub_conflict(h, hubs, line)
                hubs.add(h)
            case "connection":
                c = parse_connection(value, hubs, turn)
                if c in connection:
                    raise ParseError("Duplicated connection", line)
                connection.add(c)
            case _:
                raise ParseError(f"Type {key} not recognized", line)
    if not origin or not destination:
        raise ParseError("Start hub and end hub is mandatory")
    if not origin.capacity_defined:
        origin.capacity = nb_drones
    if nb_drones is not None:
        if nb_drones > origin.capacity:
            raise ParseError(
                "Number of drones exceed the capacity of start hub"
            )
        drones = init_drones(nb_drones, origin, destination, turn)
    try:
        sim = Simulation(
            turn=turn,
            hubs=hubs,
            origin=origin,
            destination=destination,
            connections=connection,
            drones=drones
        )
    except ValidationError as e:
        raise ParseError(f"Error creating the simulation: {e.errors(include_input=False, include_url=False)}")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Simulation created (hubs=%d, connections=%d, drones=%d)",
            len(sim.hubs), len(sim.connections), len(sim.drones)
        )
    return sim
