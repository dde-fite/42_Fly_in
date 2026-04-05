import math
import heapq
import itertools
from src.models import Hub, Simulation, Connection, HubAccess, Trajectory, DijkstraTable


def get_adyacent_hubs(hub: Hub, connections: list[Connection]
                      ) -> list[tuple[int, Hub, Connection]]:
    adc: list[tuple[int, Hub, Connection]] = []

    for con in connections:
        if hub not in con.hubs:
            continue
        end = next(iter(con.hubs - {hub}))
        if end.access == HubAccess.BLOCKED:
            continue
        d = 1
        if end.access == HubAccess.RESTRICTED:
            d = 2
        adc.append((d, end, con))
    return adc


def calculate_delay(current: Hub | Connection, other_trajectories: list[Trajectory], turn: int = 0) -> int:
    delay = 0
    return delay


def dijkstra_to_trajectory(
        table: DijkstraTable, origin: Hub, destination: Hub,
) -> Trajectory:
    trajectory: Trajectory = []
    c = table[destination]
    prev_d = c[0]
    while c[1] != origin:
        d, hub, con = c
        if con:
            for _i in range(int(prev_d - d)):
                trajectory.append(con)
        trajectory.append(c[1])
        c = table[hub]
        prev_d = d
    return trajectory


def run_dijkstra(simulation: Simulation, origin: Hub) -> DijkstraTable:
    counter = itertools.count()
    other_trajectories = [d.trajectory for d in simulation.drones if d.trajectory is not None]
    table: DijkstraTable = dict()
    for hub in simulation.hubs:
        table[hub] = (math.inf, hub, None)
    table[origin] = (0, origin, None)
    queue = [(0, 0, next(counter), origin)]
    explored: set[Hub] = set()
    while queue:
        d, _, _, hub = heapq.heappop(queue)
        if hub in explored:
            continue
        explored.add(hub)
        for ad_d, ad_hub, con in get_adyacent_hubs(hub, simulation.connections):
            if ad_hub.access == HubAccess.BLOCKED or ad_hub in explored:
                continue
            delay = calculate_delay(
                ad_hub,
                other_trajectories,
                simulation.turns
            )
            new_d = d + ad_d + delay
            if new_d < table[ad_hub][0] or ad_hub.access == HubAccess.PRIORITY:
                table[ad_hub] = (new_d, hub, con)
                bonus = 1 if ad_hub.access == HubAccess.PRIORITY else 0
                heapq.heappush(
                    queue,
                    (
                        new_d,
                        -bonus,
                        next(counter),
                        ad_hub)
                )
    return table


def calculate_route(simulation: Simulation, origin: Hub, destination: Hub,
                    ) -> Trajectory:
    table: DijkstraTable = run_dijkstra(simulation, origin)
    return dijkstra_to_trajectory(table, origin, destination)
