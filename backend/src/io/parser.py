from typing import Any
from fastapi import UploadFile
from pydantic_extra_types import Color
from src.models import Vector, HubAccess
from src.core import logger, DEBUG, ParseError
from .types import ParsedConnection, ParsedHub, ParsedMap


def parse_params(raw_params: str) -> dict[str, Any]:
    """
    Splits the parameters defined in an array of statements following this
    scheme: [key1:value1 key2=value2]. If a value in an integer, it converts
    it to int.

    Args:
        raw_params (str): Raw string delimited by '[' and ']'
    """
    value: Any
    params: dict[str, str | int] = dict()
    raw_params = raw_params.strip()
    if not raw_params or \
       not (raw_params.startswith("[") and raw_params.endswith("]")):
        raise ParseError("Params contains Syntax errors", raw_params)
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


def parse_hub(key: str, value: Any) -> ParsedHub:
    params: ParsedHub = {
        "name": "",
        "position": Vector(0, 0),
        "access": HubAccess.NORMAL.value,
        "color": None,
        "capacity": None,
        "is_origin": False,
        "is_destination": False
    }
    splits = value.split(maxsplit=3)
    if len(splits) < 3:
        raise ParseError("Syntax error for hub", f"{key} {value}")
    params["name"] = splits[0].strip()
    # Origin/Destination and Normal hub type handling
    if key == "hub":
        pass
    elif key == "start_hub":
        params["is_origin"] = True
    elif key == "end_hub":
        params["is_destination"] = True
    else:
        raise ParseError(
            f"Unknown hub type for '{params['name']}': {key}", f"{key} {value}"
        )
    # Position parsing and transformation to Vector
    try:
        params["position"] = Vector(x=int(splits[1]), y=int(splits[2]))
    except ValueError:
        raise ParseError(
            "Hub position contains an invalid integer", f"{key} {value}"
        )
    # Parsing of extra arguments
    if len(splits) == 4:
        for key, value in parse_params(splits[3]).items():
            match key:
                case "zone":
                    params["access"] = value
                case "color":
                    if not isinstance(value, str) or not value.isalpha():
                        raise ParseError(
                            f"Hub '{params['name']}' color is required to be "
                            "alphabetic",
                            f"{key} {value}"
                        )
                    if value.lower() == "rainbow":
                        params["color"] = value.lower()
                    else:
                        try:
                            params["color"] = Color(value).as_hex()
                        except ValueError:
                            raise ParseError(
                                f"Unknown color {value}",
                                f"{key} {value}"
                            )
                case "max_drones":
                    try:
                        params["capacity"] = int(value)
                    except ValueError:
                        raise ParseError(
                            f"Hub '{params['name']}' capacity is required to"
                            " be a valid number",
                            f"{key} {value}"
                        )
                case _:
                    raise ParseError(
                        f"Unknown argument for hub '{params['name']}'",
                        f"{key} {value}"
                    )
    return params


def parse_connection(raw: str) -> ParsedConnection:
    params: ParsedConnection = {
        "hubs": [],
        "capacity": None
    }
    splits = raw.split(maxsplit=2)
    # Hub name parsing
    splits = splits[0].split("-")
    if len(splits) != 2:
        raise ParseError("Syntax error for connection", raw)
    params["hubs"].append(splits[0])
    params["hubs"].append(splits[1])
    # Parsing of extra arguments
    if len(splits) == 3:
        for key, value in parse_params(splits[2]).items():
            match key:
                case "max_link_capacity":
                    params["capacity"] = value
                case _:
                    raise ParseError("Unknown argument for connection", raw)
    return params


async def parse_map(file: UploadFile) -> ParsedMap:
    params: ParsedMap = {
        "nb_drones": None,
        "hubs": [],
        "connection": []
    }
    content = await file.read()
    text = content.decode()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if len(line) < 1:
            continue
        splits = line.split(":", 1)
        if len(splits) < 2:
            raise ParseError("Map contains Syntax errors", line)
        key, value = splits
        match key.strip():
            case "nb_drones":
                if params["nb_drones"] is not None:
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
                params["nb_drones"] = int(value.strip())
            case "hub" | "start_hub" | "end_hub":
                params["hubs"].append(parse_hub(key, value))
            case "connection":
                params["connection"].append(parse_connection(value))
            case _:
                raise ParseError(f"Type {key} not recognized", line)
    if logger.isEnabledFor(DEBUG):
        logger.debug(f"Map parsed: {params}")
    return params
