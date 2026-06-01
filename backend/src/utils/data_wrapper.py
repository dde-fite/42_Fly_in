from __future__ import annotations
from typing import TYPE_CHECKING
from cachetools import TTLCache
from src.core import (KeyExpiredError, SimulationNotFound)

if TYPE_CHECKING:
    from src.models import Simulation, SimulationToken

dc: TTLCache[str, Simulation] = TTLCache(maxsize=1000, ttl=300)


def get_simulation(token: SimulationToken) -> Simulation:
    try:
        sim = dc[token]
    except (KeyError, KeyExpiredError):
        raise SimulationNotFound("Simulation not found for token")
    return sim


def set_simulation(token: SimulationToken, s: Simulation) -> None:
    dc[token] = s


def simulation_exists(token: SimulationToken) -> bool:
    return token in dc
