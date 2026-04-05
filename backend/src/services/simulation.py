from secrets import token_urlsafe
from src.models import Simulation, SimulationWithToken, Hub, Drone, Connection
from src.utils.data_cache import dc
from src.graph_routing.pathfinding import calculate_route


def register_simulation(simulation: Simulation) -> SimulationWithToken:
    token = token_urlsafe()
    dc[token] = simulation
    execute_turn(simulation)  # FOR DEBUGGING
    return SimulationWithToken(token=token, simulation=simulation)


def fetch_simulation(token: str) -> Simulation:
    return dc[token]


def update_trajectory(simulation: Simulation, drone: Drone):
    drone.trajectory = calculate_route(
        simulation, drone.hub, simulation.destination
    )


def execute_turn(simulation: Simulation, turns: int = 1) -> Simulation:
    simulation.turns += 1
    for drone in simulation.drones:
        if not drone.trajectory:
            update_trajectory(simulation, drone)
        to_print: list  = []
        for t in drone.trajectory:
            if isinstance(t, Hub):
                to_print.append(t.name)
            else:
                to_print.append([h.name for h in t.hubs])
        print(to_print)
    return simulation
