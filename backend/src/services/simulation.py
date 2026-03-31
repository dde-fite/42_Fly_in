from secrets import token_urlsafe
from src.models import Simulation, SimulationWithToken
from src.utils.data_cache import dc


def register_simulation(simulation: Simulation) -> SimulationWithToken:
    token = token_urlsafe()
    dc[token] = simulation
    return SimulationWithToken(token=token, simulation=simulation)


def fetch_simulation(token: str) -> Simulation:
    return dc[token]
