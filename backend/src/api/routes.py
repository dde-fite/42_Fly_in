from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.services import parse_map, register_simulation, fetch_simulation, execute_turn
from src.models import SimulationWithToken, Simulation, Drone
from src.utils.data_cache import KeyExpiredError
from src.core.logging import logger

router = APIRouter()


@router.post("/simulation", response_model=SimulationWithToken)
async def create_simulation(file: UploadFile):
    try:
        data = await parse_map(file)
    except ValueError as e:
        logger.debug(e)
        raise HTTPException(400, "Incorrect map format")
    await file.close()
    return register_simulation(data)


@router.get("/simulation", response_model=Simulation)
async def get_simulation(token: str):
    try:
        sim = fetch_simulation(token)
    except (KeyExpiredError, KeyError):
        raise HTTPException(404)
    return sim


@router.post("/simulation/step", response_model=list[Drone])
async def advance_simulation(token: str, steps: int = 1):
    try:
        sim = fetch_simulation(token)
    except (KeyExpiredError, KeyError):
        raise HTTPException(404)
    execute_turn(sim, steps)
    return sim.drones
