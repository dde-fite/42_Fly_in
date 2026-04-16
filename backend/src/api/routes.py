from fastapi import APIRouter, HTTPException, UploadFile
from src.models import SimulationToken
from src.services import (
    register_simulation, fetch_simulation, execute_turn,
    fetch_hub, fetch_drone, fetch_connection
)
from src.schema import (
    ResponseSimulation, ResponseDrone, DroneRef, ResponseHub,
    HubRef, ConnectionRef, ResponseConnection
)
from src.core import ParseError, SimulationAlreadyAllocated, SimulationNotFound

router = APIRouter()


@router.get("/token")
def generate_token():
    import secrets
    return secrets.token_urlsafe(32) + f"Len: {len(secrets.token_urlsafe(32))}"

@router.post("/simulation", response_model=ResponseSimulation)
async def create_simulation(token: SimulationToken, file: UploadFile):
    try:
        s = register_simulation(token, file)
    except ParseError as e:
        raise HTTPException(
            400,
            f"Error parsing map: {e.msg} in line: {e.line}"
        )
    except SimulationAlreadyAllocated:
        raise HTTPException(400)
    return await s


@router.get("/simulation", response_model=ResponseSimulation)
async def get_simulation(token: SimulationToken):
    try:
        return fetch_simulation(token)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.get("/hub", response_model=ResponseHub)
async def get_hub(token: SimulationToken, id: HubRef):
    try:
        return fetch_hub(token, id)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.get("/drone", response_model=ResponseDrone)
async def get_drone(token: SimulationToken, id: DroneRef):
    try:
        return fetch_drone(token, id)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.get("/connection", response_model=ResponseConnection)
async def get_connection(token: SimulationToken, id: ConnectionRef):
    try:
        return fetch_connection(token, id)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")


@router.post("/simulation/step", response_model=ResponseSimulation)
async def advance_simulation(token: str, steps: int):
    try:
        return execute_turn(token, steps)
    except SimulationNotFound:
        raise HTTPException(404, "Simulation not found for token")
