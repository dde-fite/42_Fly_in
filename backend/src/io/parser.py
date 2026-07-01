from typing import Any
from fastapi import UploadFile
from pydantic_extra_types import Color
from src.models import Vector, HubAccess
from src.core import logger, DEBUG, config, ParseError
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


def parse_nb_drones(value: str) -> int:
    """
    Parse the number of drones from a string.

    Args:
        value (str): String containing the number of drones.
    """
    value = value.strip()
    if not value.isdigit():
        raise ParseError(
            "Number of drones does not contain a valid positive integer",
            value
        )
    return int(value)


def parse_hub(key: str, value: Any) -> ParsedHub:
    """
    Parse a hub definition line into a ParsedHub dict.

    Args:
        key (str): Hub type prefix — one of ``"hub"``, ``"start_hub"``,
            or ``"end_hub"``.
        value (str): Remainder of the line after the colon, e.g.
            ``" roof1 3 4 [zone=restricted color=red]"``.

    Returns:
        ParsedHub: Dict with name, position, access, color, capacity,
            is_origin, and is_destination fields populated.

    Raises:
        ParseError: On any syntax error, unknown hub type, invalid
            coordinates, or unrecognised metadata key.
    """
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
                    try:
                        params["access"] = HubAccess(value).value
                    except ValueError:
                        raise ParseError(
                            f"Hub '{params['name']}' access type is unknown",
                            f"{key} {value}"
                        )
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
    """
    Parse a raw connection line into a ParsedConnection dict.

    Args:
        raw (str): Raw value string after the ``connection:`` prefix,
            e.g. ``"hub1-hub2 [max_link_capacity=2]"``.

    Returns:
        ParsedConnection: Dict with ``hubs`` (two hub names) and optional
            ``capacity``.

    Raises:
        ParseError: If the hub pair syntax is wrong or an unknown argument
            is provided.
    """
    params: ParsedConnection = {
        "hubs": [],
        "capacity": None
    }
    outer_splits = raw.split(maxsplit=1)
    # Hub name parsing
    hub_pair = outer_splits[0].split("-")
    if len(hub_pair) != 2:
        raise ParseError("Syntax error for connection", raw)
    params["hubs"].append(hub_pair[0])
    params["hubs"].append(hub_pair[1])
    # Parsing of extra arguments
    if len(outer_splits) == 2:
        for key, value in parse_params(outer_splits[1]).items():
            match key:
                case "max_link_capacity":
                    params["capacity"] = value
                case _:
                    raise ParseError("Unknown argument for connection", raw)
    return params


async def parse_map(file: UploadFile) -> ParsedMap:
    """
    Parse an uploaded map file into a ParsedMap dict.

    Reads the file content, strips comments (lines starting with ``#``),
    and dispatches each directive to the appropriate parser. Raises
    ParseError on any syntax or semantic violation.

    Args:
        file (UploadFile): The uploaded plain-text map file.

    Returns:
        ParsedMap: Dict containing ``nb_drones``, ``hubs``, and
            ``connection`` lists ready for Simulation construction.

    Raises:
        ParseError: On any unrecognised directive, duplicate ``nb_drones``,
            undeclared hub reference, or invalid metadata.
    """
    strict_first_meaningful_line = True
    strict_hubs_declared: list[str] = []
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
                if config.STRICT_PARSER:
                    if not strict_first_meaningful_line:
                        raise ParseError(
                            "Strict mode error - nb_drones has to at the top"
                            "of the file",
                            line
                        )
                if params["nb_drones"] is not None:
                    raise ParseError(
                        "Number of drones can not be declared more"
                        " than 1 time",
                        line
                    )
                nb = parse_nb_drones(value)
                params["nb_drones"] = nb
            case "hub" | "start_hub" | "end_hub":
                h = parse_hub(key, value)
                if config.STRICT_PARSER:
                    strict_hubs_declared.append(h["name"])
                params["hubs"].append(h)
            case "connection":
                c = parse_connection(value)
                # If strict mode is enabled, check if hubs were declared
                if config.STRICT_PARSER:
                    for h_name in c["hubs"]:
                        if h_name not in strict_hubs_declared:
                            raise ParseError(
                                f"Strict mode error - hub '{h_name}' is not"
                                " declared for connection"
                                f"'{c['hubs'][0]}<->{c['hubs'][1]}'",
                                line
                            )
                params["connection"].append(c)
            case _:
                raise ParseError(f"Type {key} not recognized", line)
        strict_first_meaningful_line = False
    if logger.isEnabledFor(DEBUG):
        logger.debug(f"Map parsed: {params}")
    return params
