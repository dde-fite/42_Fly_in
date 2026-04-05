import math
from src.models import Hub, Simulation, Connection, HubAccess, Trajectory, DijkstraTable


def get_adyacent_hubs(hub: Hub, connections: list[Connection]
                      ) -> list[tuple[Hub, int]]:
    adc: list[tuple[Hub, int]] = []

    for con in connections:
        if hub not in con.hubs:
            continue
        end = next(h for h in con.hubs if h != hub)
        if end.access == HubAccess.BLOCKED:
            continue
        cost = 1
        if end.access == HubAccess.RESTRICTED:
            cost = 2
        adc.append((end, cost))
    return adc


def calculate_delay():
    return 0


def dijkstra_to_trajectory(
        table: DijkstraTable, origin: Hub, destination: Hub
) -> Trajectory:
    trajectory: Trajectory = []
    selected = destination
    while selected != origin:
        trajectory.insert(0, selected)
        selected = table[selected][0]
    return trajectory


def run_dijkstra(simulation: Simulation, origin: Hub) -> DijkstraTable:
    table: DijkstraTable = dict()
    for hub in simulation.hubs:
        table[hub] = (origin, math.inf)
    table[origin] = (origin, 0)
    open = simulation.hubs.copy()
    selected = origin
    while len(open) > 0:
        open.remove(selected)
        adyacent_hubs = get_adyacent_hubs(selected, simulation.connections)
        for hub, cost in adyacent_hubs:
            if hub not in open:
                continue
            new_cost = cost + table[selected][1] + calculate_delay()
            if (new_cost < table[hub][1] and table[selected][0].access != HubAccess.PRIORITY):
                table[hub] = (selected, new_cost)
        if not open:
            break
        # Use calculate_delays when comparing or adding a new record in table.
        selected = min(open, key=lambda h: table[h][1])
    return table


def calculate_route(simulation: Simulation, origin: Hub, destination: Hub,
                    ) -> Trajectory:
    table: DijkstraTable = run_dijkstra(simulation, origin)
    return dijkstra_to_trajectory(table, origin, destination)
