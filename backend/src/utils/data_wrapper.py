from __future__ import annotations
from typing import TYPE_CHECKING, cast
from cachetools import TTLCache
from src.core import (KeyExpiredError, SimulationNotFound)

if TYPE_CHECKING:
    from src.models import Simulation, SimulationToken

dc: TTLCache[str, Simulation] = TTLCache(maxsize=1000, ttl=300)


def get_simulation(token: SimulationToken) -> Simulation:
    """
    Retrieve the simulation associated with *token* from the in-memory cache.

    Args:
        token (SimulationToken): The session token identifying the simulation.

    Returns:
        Simulation: The cached Simulation instance.

    Raises:
        SimulationNotFound: If no simulation exists for the token or the
            entry has expired.
    """
    try:
        sim: Simulation = cast("Simulation", dc[token])
    except (KeyError, KeyExpiredError):
        raise SimulationNotFound("Simulation not found for token")
    return sim


def set_simulation(token: SimulationToken, s: Simulation) -> None:
    """
    Store *s* in the in-memory cache keyed by *token*.

    Args:
        token (SimulationToken): The session token to associate with the
            simulation.
        s (Simulation): The Simulation instance to cache.
    """
    dc[token] = s


def simulation_exists(token: SimulationToken) -> bool:
    """
    Check if a simulation exists for *token* in the in-memory cache.

    Args:
        token (SimulationToken): The session token to check.
    """
    return token in dc
