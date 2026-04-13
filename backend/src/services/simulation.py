from fastapi import UploadFile
from pydantic import Base64UrlStr
from src.core import SimulationAlreadyAllocated, SimulationNotFound
from src.schema import ResponseSimulation, ResponseDrone, ResponseHub, DroneRef, HubRef
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


def fetch_simulation(token: Base64UrlStr) -> ResponseSimulation | None:
    s = dc.get(token)
    if not s:
        return None
    return simulation_to_schema(s)


def fetch_drone(token: Base64UrlStr, id: DroneRef) -> ResponseDrone | None:
    s: Simulation | None = dc.get(token)
    if not s:
        return None
    for drone in s.drones:
        if drone.id == id:
            return drone
    return None


def fetch_hub(token: Base64UrlStr, id: HubRef) -> ResponseHub | None:
    s: Simulation | None = dc.get(token)
    if not s:
        return None
    for hub in s.hubs:
        if hub.id == id:
            return hub
    return None


def execute_turn(token: Base64UrlStr, turns: int = 1) -> Simulation:
    s = fetch_simulation(token)
    if not s:
        raise SimulationNotFound()
    s.turns += 1
    return s
