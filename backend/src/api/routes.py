from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.services import parse_map, register_simulation, fetch_simulation, execute_turn
from src.models import SimulationWithToken, Simulation
from src.utils.data_cache import KeyExpiredError

router = APIRouter()


@router.post("/simulation", response_model=SimulationWithToken)
async def create_simulation(file: UploadFile):
    try:
        data = await parse_map(file)
    except ValueError:
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


@router.post("/simulation/step")
async def advance_simulation(token: str, steps: int = 1):
    try:
        sim = execute_turn(token, steps)
    except (KeyExpiredError, KeyError):
        raise HTTPException(404)
    return sim
