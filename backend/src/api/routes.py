from uuid import UUID
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, UploadFile
from src.models import SimulationToken
from src.services import (
    register_simulation, fetch_simulation, execute_turn,
    fetch_hub, fetch_drone, fetch_connection
)
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    ResponseConnection
)
from src.core.errors import ParseError, SimulationAlreadyAllocated, SimulationNotFound, SimulationConflict

router = APIRouter()


# ---- debug ----
@router.get("/token")
def generate_token() -> str:
    import secrets
    token = secrets.token_urlsafe(32)
    return token + f"  Len: {len(token)}"
# ---------------


# Simulation
@router.get("/simulation", response_model=ResponseSimulation)
async def get_simulation(token: SimulationToken) -> ResponseSimulation:
    try:
        return fetch_simulation(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.post("/simulation", response_model=ResponseSimulation)
async def create_simulation(
    token: SimulationToken, file: UploadFile
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


@router.post("/simulation/step", response_model=ResponseSimulation)
async def advance_simulation(
    token: SimulationToken, steps: int
) -> ResponseSimulation:
    try:
        return execute_turn(token, steps)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# Hubs
@router.get("/hub", response_model=ResponseHub)
async def get_hub(token: SimulationToken, id: UUID) -> ResponseHub:
    try:
        h = fetch_hub(token, id)
        if not h:
            raise HTTPException(404, "Hub not found")
        return h
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# Drone
@router.get("/drone", response_model=ResponseDrone)
async def get_drone(token: SimulationToken, id: UUID) -> ResponseDrone:
    try:
        d = fetch_drone(token, id)
        if not d:
            raise HTTPException(404, "Drone not found")
        return d
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


# Connection
@router.get("/connection", response_model=ResponseConnection)
async def get_connection(
    token: SimulationToken, id: UUID
) -> ResponseConnection:
    try:
        c = fetch_connection(token, id)
        if not c:
            raise HTTPException(404, "Connection not found")
        return c
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")
