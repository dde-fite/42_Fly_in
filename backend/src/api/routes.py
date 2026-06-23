import secrets
from uuid import UUID
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Query, UploadFile
from src.models import SimulationToken
from src.services import (
    register_simulation, fetch_simulation, execute_turn,
    fetch_hubs, fetch_drones, fetch_connections, fetch_itineraries
)
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    ResponseConnection, ResponseItinerary
)
from src.core.errors import (
    ParseError, SimulationAlreadyAllocated, SimulationNotFound,
    SimulationConflict
)

router = APIRouter()

_TOKEN_QUERY = Query(
    ...,
    min_length=43,
    max_length=43,
    pattern=r'^[A-Za-z0-9_-]{43}$',
    description="Authentication token that identifies the simulation session.",
)


# ---- debug ----
@router.get(
    "/token",
    summary="Generate a random token",
    description=(
        "Development helper. Returns a cryptographically secure random token "
        "together with its length. Use the token value as the `token` query "
        "parameter in the other endpoints."
    ),
    tags=["Simulation"],
    include_in_schema=True,
)
def generate_token() -> str:
    """Generate a cryptographically secure random URL-safe token."""
    token = secrets.token_urlsafe(32)
    return token
# ---------------


# ── Simulation ───────────────────────────────────────────────────────────────

@router.get(
    "/simulation",
    response_model=ResponseSimulation,
    summary="Get simulation state",
    description=(
        "Returns the current state of the simulation associated with the "
        "given token, including all hubs, connections and drones."
    ),
    responses={
        200: {"description": "Current simulation state."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Simulation"],
)
async def get_simulation(
    token: SimulationToken = _TOKEN_QUERY,
) -> ResponseSimulation:
    """Return the current state of the simulation for *token*."""
    try:
        return fetch_simulation(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.post(
    "/simulation",
    response_model=ResponseSimulation,
    summary="Create a simulation from a map file",
    description=(
        "Parses the uploaded map file and registers a new simulation for the "
        "given token. The map must be a plain-text `.txt` file following the "
        "simulation map format (`nb_drones`, `start_hub`, `end_hub`, `hub`, "
        "`connection` directives). Each token can hold at most one simulation "
        "at a time."
    ),
    responses={
        200: {"description": "Simulation created successfully."},
        400: {"description": "Map file could not be parsed (syntax error)."},
        409: {"description": "A simulation already exists for this token."},
        422: {"description": (
            "Map values are invalid or produce a logical conflict "
            "(e.g. duplicate hubs, capacity violations)."
        )},
    },
    tags=["Simulation"],
)
async def create_simulation(
    file: UploadFile,
    token: SimulationToken = _TOKEN_QUERY,
) -> ResponseSimulation:
    """Parse *file* and register a new simulation for *token*."""
    try:
        return await register_simulation(token, file)
    except ParseError as e:
        raise HTTPException(
            400,
            f"Error parsing map: {e.msg} in line: {e.line}"
        )
    except ValidationError as e:
        raise HTTPException(
            422,
            f"Incorrect values in map: {e.errors(include_url=False)}"
        )
    except SimulationAlreadyAllocated:
        raise HTTPException(
            409,
            "A simulation is already registered for this token"
        )
    except SimulationConflict as e:
        raise HTTPException(
            422,
            f"Simulation conflict: {e}"
        )


@router.post(
    "/simulation/step",
    response_model=ResponseSimulation,
    summary="Advance the simulation by N steps",
    description=(
        "Executes the given number of turns on the simulation associated with "
        "the token. Each turn: itineraries are validated, the traffic "
        "controller assigns routes to unrouted drones, drones move, "
        "zones purge expired bookings, and the turn counter is incremented. "
        "Returns the simulation state after all steps have been applied."
    ),
    responses={
        200: {"description": "Simulation state after the requested steps."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Simulation"],
)
async def advance_simulation(
    token: SimulationToken = _TOKEN_QUERY,
    steps: int = Query(
        default=1, ge=1,
        description="Number of turns to advance. Must be a positive integer.",
    ),
) -> ResponseSimulation:
    """Advance the simulation by *steps* turns and return the new state."""
    try:
        return execute_turn(token, steps)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Hubs ─────────────────────────────────────────────────────────────────────

@router.get(
    "/hubs",
    response_model=dict[UUID, ResponseHub],
    summary="Get all hubs",
    description=(
        "Returns every hub of the simulation associated with the token, keyed "
        "by its UUID. Each hub includes name, position, capacity, access, "
        "color and connected drones."
    ),
    responses={
        200: {"description": "All hubs keyed by UUID."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Hubs"],
)
async def get_hubs(
    token: SimulationToken = _TOKEN_QUERY,
) -> dict[UUID, ResponseHub]:
    """Return all hubs for the simulation associated with *token*."""
    try:
        return fetch_hubs(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Drones ───────────────────────────────────────────────────────────────────

@router.get(
    "/drones",
    response_model=dict[UUID, ResponseDrone],
    summary="Get all drones",
    description=(
        "Returns every drone of the simulation for the token, keyed "
        "by its UUID. Each drone includes location and destination."
    ),
    responses={
        200: {"description": "All drones keyed by UUID."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Drones"],
)
async def get_drones(
    token: SimulationToken = _TOKEN_QUERY,
) -> dict[UUID, ResponseDrone]:
    """Return all drones for the simulation associated with *token*."""
    try:
        return fetch_drones(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Connections ──────────────────────────────────────────────────────────────

@router.get(
    "/connections",
    response_model=dict[UUID, ResponseConnection],
    summary="Get all connections",
    description=(
        "Returns every connection of the simulation for the token, "
        "keyed by its UUID. Includes the two endpoint hubs and capacity."
    ),
    responses={
        200: {"description": "All connections keyed by UUID."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Connections"],
)
async def get_connections(
    token: SimulationToken = _TOKEN_QUERY,
) -> dict[UUID, ResponseConnection]:
    """Return all connections for the simulation associated with *token*."""
    try:
        return fetch_connections(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Itineraries ──────────────────────────────────────────────────────────────

@router.get(
    "/itineraries",
    response_model=dict[UUID, ResponseItinerary],
    summary="Get all itineraries",
    description=(
        "Returns every active itinerary for the simulation token, keyed "
        "by its UUID. Each itinerary lists booked slots in travel order "
        "with zone, kind, and enter/exit turns."
    ),
    responses={
        200: {"description": "All itineraries keyed by UUID."},
        404: {"description": "No simulation found for the provided token."},
    },
    tags=["Itineraries"],
)
async def get_itineraries(
    token: SimulationToken = _TOKEN_QUERY,
) -> dict[UUID, ResponseItinerary]:
    """Return all active itineraries for the simulation of *token*."""
    try:
        return fetch_itineraries(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")
