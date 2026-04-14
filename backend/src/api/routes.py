from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import Base64UrlStr
from src.services import register_simulation, fetch_simulation, execute_turn, fetch_hub
from src.schema import ResponseSimulation, ResponseDrone, DroneRef, ResponseHub, ResponseTransit, HubRef, ConnectionRef, ResponseConnection, 
from src.core import ParseError, SimulationAlreadyAllocated

router = APIRouter()


@router.post("/simulation", response_model=ResponseSimulation)
async def create_simulation(token: Base64UrlStr, file: UploadFile):
    try:
        s = register_simulation(token, file)
    except ParseError:
        raise HTTPException(400, "Incorrect map format")
    except SimulationAlreadyAllocated:
        raise HTTPException(400)
    return await s


@router.get("/simulation", response_model=ResponseSimulation)
async def get_simulation(token: Base64UrlStr):
    s = fetch_simulation(token)
    if not s:
        raise HTTPException(404)
    return s


@router.get("/hub", response_model=ResponseHub)
async def get_hub(token: Base64UrlStr, id: HubRef):
    s = fetch_hub(token)
    if not s:
        raise HTTPException(404)
    return s


@router.get("/drone", response_model=ResponseDrone)
async def get_drone(token: Base64UrlStr, id: DroneRef):
    s = fetch_simulation(token)
    if not s:
        raise HTTPException(404)
    return s


@router.get("/connection", response_model=ResponseConnection)
async def get_connection(token: Base64UrlStr, id: DroneRef):
    s = fetch_simulation(token)
    if not s:
        raise HTTPException(404)
    return s


@router.post("/simulation/step", response_model=list[Drone])
async def advance_simulation(token: str, steps: int = 1):
    try:
        sim = fetch_simulation(token)
    except (KeyExpiredError, KeyError):
        raise HTTPException(404)
    execute_turn(sim, steps)
    return sim.drones
