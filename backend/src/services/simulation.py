from secrets import token_urlsafe
from src.models import Simulation, SimulationWithToken
from src.utils.data_cache import dc
from src.graph_routing.pathfinding import calculate_route


def register_simulation(simulation: Simulation) -> SimulationWithToken:
    token = token_urlsafe()
    dc[token] = simulation
    return SimulationWithToken(token=token, simulation=simulation)


def fetch_simulation(token: str) -> Simulation:
    return dc[token]


def execute_turn(token: str, turns: int) -> Simulation:
    sim = fetch_simulation(token)
    sim.turns += 1
    for drone in sim.drones:
        print([t.name for t in calculate_route(sim, sim.origin, sim.destination)])
    return sim
