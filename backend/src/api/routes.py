from uuid import UUID
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Query, UploadFile
from src.models import SimulationToken
from src.services import (
    register_simulation, fetch_simulation, execute_turn,
    fetch_hub, fetch_drone, fetch_connection
)
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    ResponseConnection
)
from src.core.errors import (
    ParseError, SimulationAlreadyAllocated, SimulationNotFound,
    SimulationConflict
)

router = APIRouter()


# ---- debug ----
@router.get(
    "/token",
    summary="Generate a random token",
    description=(
        "Development helper. Returns a cryptographically secure random token "
        "together with its length. Use the token value as the `token` query "
        "parameter in the other endpoints."
    ),
    tags=["Debug"],
    include_in_schema=True,
)
def generate_token() -> str:
    import secrets
    token = secrets.token_urlsafe(32)
    return token + f"  Len: {len(token)}"
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
    token: SimulationToken = Query(..., description="Authentication token that identifies the simulation session."),
) -> ResponseSimulation:
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
        409: {"description": "A simulation is already registered for this token."},
        422: {"description": "Map values are invalid or produce a logical conflict (e.g. duplicate hubs, capacity violations)."},
    },
    tags=["Simulation"],
)
async def create_simulation(
    token: SimulationToken = Query(..., description="Authentication token that will own the new simulation."),
    file: UploadFile = ...,
) -> ResponseSimulation:
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
    except SimulationConflict as e:
        raise HTTPException(
            422,
            f"Simulation conflict: {e}"
        )
    except SimulationAlreadyAllocated:
        raise HTTPException(
            409,
            "Simulation is already allocated for token")


@router.post(
    "/simulation/step",
    response_model=ResponseSimulation,
    summary="Advance the simulation by N steps",
    description=(
        "Executes the given number of turns on the simulation associated with "
        "the token. Each turn: itineraries are validated, the traffic "
        "controller assigns routes to unrouted drones, drones attempt to move, "
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
    token: SimulationToken = Query(..., description="Authentication token that identifies the simulation session."),
    steps: int = Query(default=1, ge=1, description="Number of turns to advance. Must be a positive integer."),
) -> ResponseSimulation:
    try:
        return execute_turn(token, steps)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Hubs ─────────────────────────────────────────────────────────────────────

@router.get(
    "/hub",
    response_model=ResponseHub,
    summary="Get hub by ID",
    description=(
        "Returns the details of a single hub (name, position, capacity, "
        "access zone, color, connected drones) identified by its UUID within "
        "the simulation associated with the token."
    ),
    responses={
        200: {"description": "Hub details."},
        404: {"description": "Simulation not found for the token, or no hub with the given ID exists."},
    },
    tags=["Hubs"],
)
async def get_hub(
    token: SimulationToken = Query(..., description="Authentication token that identifies the simulation session."),
    id: UUID = Query(..., description="UUID of the hub to retrieve."),
) -> ResponseHub:
    try:
        h = fetch_hub(token, id)
        if not h:
            raise HTTPException(404, "Hub not found")
        return h
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Drones ───────────────────────────────────────────────────────────────────

@router.get(
    "/drone",
    response_model=ResponseDrone,
    summary="Get drone by ID",
    description=(
        "Returns the details of a single drone (current location, destination, "
        "itinerary status) identified by its UUID within the simulation "
        "associated with the token."
    ),
    responses={
        200: {"description": "Drone details."},
        404: {"description": "Simulation not found for the token, or no drone with the given ID exists."},
    },
    tags=["Drones"],
)
async def get_drone(
    token: SimulationToken = Query(..., description="Authentication token that identifies the simulation session."),
    id: UUID = Query(..., description="UUID of the drone to retrieve."),
) -> ResponseDrone:
    try:
        d = fetch_drone(token, id)
        if not d:
            raise HTTPException(404, "Drone not found")
        return d
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# ── Connections ──────────────────────────────────────────────────────────────

@router.get(
    "/connection",
    response_model=ResponseConnection,
    summary="Get connection by ID",
    description=(
        "Returns the details of a single connection (the two hubs it links, "
        "capacity, current drone occupancy) identified by its UUID within the "
        "simulation associated with the token."
    ),
    responses={
        200: {"description": "Connection details."},
        404: {"description": "Simulation not found for the token, or no connection with the given ID exists."},
    },
    tags=["Connections"],
)
async def get_connection(
    token: SimulationToken = Query(..., description="Authentication token that identifies the simulation session."),
    id: UUID = Query(..., description="UUID of the connection to retrieve."),
) -> ResponseConnection:
    try:
        c = fetch_connection(token, id)
        if not c:
            raise HTTPException(404, "Connection not found")
        return c
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")
