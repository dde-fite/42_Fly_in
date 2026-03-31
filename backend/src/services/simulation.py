from secrets import token_urlsafe
from src.models import Simulation, SimulationWithToken
from src.utils.data_cache import dc


def register_simulation(simulation: Simulation) -> SimulationWithToken:
    token = token_urlsafe()
    dc[token] = simulation
    return SimulationWithToken(token=token, simulation=simulation)


def fetch_simulation(token: str) -> Simulation:
    return dc[token]


def execute_turn(token: str, turns: int) -> Simulation:
    sim = fetch_simulation(token)
    sim.turns += 1
    return sim
