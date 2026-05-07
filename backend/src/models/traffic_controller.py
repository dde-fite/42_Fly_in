from __future__ import annotations
import heapq
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from src.core.errors import TrafficError, ZoneNotAvailable
from .turn import Turn
from .itinerary import Itinerary
from .hub import Hub, HubCost

if TYPE_CHECKING:
    from .drone import Drone
    from .simulation import Simulation


@dataclass(order=True)
class _DijkstraNode:
    """
    Priority-queue entry for the Dijkstra search.

    ``arrival_turn`` is the cost dimension being minimised: the earliest
    simulated turn at which the drone can *arrive* at ``hub`` after having
    traversed all intermediate zones (including any wait time imposed by
    existing bookings).

    ``hub`` and ``path`` are tiebreakers / payload and are excluded from
    ordering so that the dataclass comparison only uses ``arrival_turn``.
    """
    arrival_turn: int
    hub: Hub = field(compare=False)
    path: list[Hub] = field(compare=False)


class TrafficController:
    """
    Central authority that assigns routes (Itineraries) to drones.

    Path-finding:
        Uses **Dijkstra's algorithm** where the edge weight between two hubs is
        NOT a static number but the *real temporal cost* experienced at
        planning time: the algorithm queries each zone for its next available
        entry/exit slot (exactly as the Itinerary builder does) and
        accumulates the actual turn number at which the drone would arrive at
        each hub.

        This means congested zones are naturally avoided: if a connection or
        hub is fully booked for the next 5 turns, those 5 extra wait turns are
        reflected in the path cost and Dijkstra will prefer an alternative
        route with fewer delays, even if it has more hops.

        Blocked hubs (movement cost = None) are pruned from the search
        entirely.

        After the optimal path is found the controller attempts to instantiate
        an Itinerary (which actually books the slots). If booking fails for any
        reason the next-best candidate path is tried (fallback list built
        during the search).
    """
    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_itinerary(
        self,
        drone: Drone,
        simulation: Simulation,
    ) -> Itinerary | None:
        """
        Find the time-optimal route for *drone* and book it as an Itinerary.

        Returns the new Itinerary on success, or None if no viable route
        exists right now.
        """
        origin = drone.location
        if not isinstance(origin, Hub):
            # Drone is mid-connection; wait until it lands on a hub.
            return None
        if origin == drone.destination:
            return None
        ranked_paths = self.dijkstra(origin, drone.destination, drone.turn)
        for hub_path, _ in ranked_paths:
            try:
                return Itinerary(drone, hub_path, drone.turn)
            except (ZoneNotAvailable, TrafficError):
                continue
        return None

    # ------------------------------------------------------------------
    # Dijkstra
    # ------------------------------------------------------------------

    def dijkstra(
        self,
        origin: Hub,
        destination: Hub,
        current_turn: Turn,
    ) -> list[tuple[list[Hub], int]]:
        """
        Run Dijkstra from *origin* to *destination* starting at *current_turn*.

        The cost of reaching a hub is the simulated arrival turn, computed by
        asking each intermediate zone for its next available entry and exit
        slots — the same queries the Itinerary builder uses — so the cost
        accounts for real congestion delays.

        Returns a list of ``(hub_path, arrival_turn)`` tuples sorted by
        ascending arrival turn (best route first). All discovered paths to
        *destination* are returned so that ``request_itinerary`` can fall back
        to the second-best route if the best one fails to book.
        """
        # best_arrival[hub] = lowest arrival turn seen so far for that hub.
        best_arrival: dict[Hub, int] = {}
        # All complete paths found, each with its arrival turn.
        found: list[tuple[list[Hub], int]] = []
        # Min-heap seeded with the origin at the current turn.
        heap: list[_DijkstraNode] = []
        heapq.heappush(heap, _DijkstraNode(
            arrival_turn=current_turn.value,
            hub=origin,
            path=[origin],
        ))
        while heap:
            node = heapq.heappop(heap)
            arr = node.arrival_turn
            hub = node.hub
            path = node.path
            # Skip if we already found a better way to reach this hub.
            if hub in best_arrival and best_arrival[hub] <= arr:
                continue
            best_arrival[hub] = arr
            if hub == destination:
                found.append((path, arr))
                # Keep searching for alternative paths to use as fallback.
                continue
            # Expand neighbours through their shared connections.
            for c in hub.connections:
                neighbour = c.other_hub(hub)
                if HubCost.get(neighbour.access) is None:
                    continue
                # Avoid cycles within this path.
                if neighbour in path:
                    continue
                # ── Simulate the temporal cost through this connection ──
                #
                # 1. Earliest turn the drone can enter the connection from
                #    its current hub (may be delayed by existing bookings).
                conn_entry: Turn = c.get_next_available_entry(
                    Turn(arr)
                )
                # 2. Earliest turn the drone can exit the connection into
                #    the neighbour hub (factors in minimum traversal cost
                #    = HubCost[neighbour.access] and connection capacity).
                conn_exit: Turn = c.get_next_available_exit(
                    conn_entry, neighbour
                )
                # 3. Earliest turn the drone can enter the neighbour hub
                #    (the hub itself may also be congested).
                hub_entry: Turn = neighbour.get_next_available_entry(conn_exit)
                neighbour_arrival = hub_entry.value
                # Only enqueue if this is a better route to the neighbour.
                if neighbour in best_arrival and best_arrival[neighbour] <= neighbour_arrival:
                    continue
                heapq.heappush(heap, _DijkstraNode(
                    arrival_turn=neighbour_arrival,
                    hub=neighbour,
                    path=path + [neighbour],
                ))
        # Dijkstra naturally discovers routes in cost order, but sort
        # explicitly to make the guarantee clear to callers.
        found.sort(key=lambda t: t[1])
        return found

    # ------------------------------------------------------------------
    # Tick integration
    # ------------------------------------------------------------------

    def tick(self, simulation: Simulation) -> None:
        """
        Called once per simulation turn.

        Assigns itineraries to every drone that currently lacks one (or whose
        itinerary has expired).
        """
        for drone in simulation.drones:
            if drone.itinerary is None or not drone.itinerary.is_operative:
                self.request_itinerary(drone, simulation)
