from fastapi import UploadFile
from pydantic import Base64UrlStr
from src.core import SimulationAlreadyAllocated, SimulationNotFound
from src.schema import ResponseSimulation
from src.models import Simulation
from src.utils.data_cache import dc
from src.mappers import simulation_to_schema
from src.utils import parse_map


async def register_simulation(
        token: Base64UrlStr,
        file: UploadFile
) -> ResponseSimulation:
    if dc.get(token):
        raise SimulationAlreadyAllocated(f"Token {token} already allocated!")
    s = await parse_map(file)
    await file.close()
    dc[token] = s
    return simulation_to_schema(s)


def fetch_simulation(token: Base64UrlStr) -> Simulation | None:
    return dc.get(token)


def execute_turn(token: Base64UrlStr, turns: int = 1) -> Simulation:
    s = fetch_simulation(token)
    if not s:
        raise SimulationNotFound()
    s.turns += 1
    return s
