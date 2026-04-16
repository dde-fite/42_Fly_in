from .data_cache import dc
from src.core import (KeyExpiredError, SimulationNotFound)
from src.models import Simulation, SimulationToken


def get_simulation(token: SimulationToken) -> Simulation:
    try:
        return dc[token]
    except (KeyError, KeyExpiredError):
        raise SimulationNotFound("Simulation not found for token")


def set_simulation(token: SimulationToken, s: Simulation) -> None:
    dc[token] = s


def simulation_exists(token: SimulationToken) -> bool:
    return token in dc
