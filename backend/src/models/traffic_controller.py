from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.errors import TrafficError, ZoneNotAvailable
from .hub import Hub, HubCost
from .itinerary import Itinerary
from .turn import Turn

if TYPE_CHECKING:
    from .drone import Drone
    from .simulation import Simulation


# Maximum turns to search ahead when a zone is congested.
# Prevents infinite loops on unsolvable or saturated graphs.
_MAX_WAIT: int = 10_000


@dataclass(order=True)
class _Node:
    """
    Priority-queue entry for the time-aware Dijkstra search.

    Only ``arrival_turn`` participates in heap ordering.  The remaining
    fields are payload and are excluded from comparison via ``compare=False``.
    Using a plain integer cost avoids floating-point issues and makes tie
    breaking deterministic.
    """

    arrival_turn: int
    hub: Hub = field(compare=False)
    # Ancestor set stored as frozenset for O(1) membership tests, plus the
    # ordered list for building the final hub path on arrival.
    visited: frozenset[Hub] = field(compare=False)
    path: list[Hub] = field(compare=False)


class TrafficController:
    """
    Central authority that assigns time-optimal routes (:class:`Itinerary`)
    to drones that currently lack one.

    Algorithm
    ---------
    Path-finding uses a **time-aware Dijkstra** where edge weights are *not*
    static hop counts but the real temporal cost at planning time: each zone
    is queried for its next available entry/exit slot, accounting for existing
    bookings and capacity limits.  Congested zones are therefore penalised
    naturally by the extra wait time they impose.

    After the shortest path is found the controller tries to book it via
    :class:`Itinerary`.  If the booking fails (race condition between planning
    and booking), it falls back to the next-best candidate.

    Correctness guarantees
    ----------------------
    * Blocked hubs (``HubCost → None``) are pruned at expansion time.
    * Cycles are avoided per-path via a ``frozenset`` membership test (O(1)).
    * A ``_MAX_WAIT`` cap on inner availability loops prevents live-lock.
    * The destination node is not pruned on first visit so alternative paths
      can still be collected as fallbacks, while ``best_arrival`` still prunes
      strictly dominated routes.
    """

    def __init__(self, simulation: Simulation) -> None:
        self.__simulation = simulation

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_itinerary(
        self,
        drone: Drone,
    ) -> Itinerary | None:
        """
        Find and book the time-optimal route for *drone*.

        Returns the new :class:`Itinerary` on success, or ``None`` when:

        * the drone is mid-connection (must wait until it reaches a hub), or
        * the drone is already at its destination, or
        * no viable route exists (graph disconnected, all paths blocked).
        """
        origin = drone.location

        # Route planning is only valid from a hub; connections are mid-transit.
        if not isinstance(origin, Hub):
            return None

        if origin == drone.destination:
            return None

        ranked_paths = self._dijkstra(origin, drone.destination, drone.turn)

        for hub_path, _ in ranked_paths:
            try:
                return Itinerary(drone, hub_path, drone.turn)
            except (ZoneNotAvailable, TrafficError):
                # Booking failed (e.g. another drone grabbed the slot between
                # planning and committing).  Try the next candidate.
                continue

        return None

    # ------------------------------------------------------------------
    # Tick integration
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """
        Called once per simulation turn by :class:`Simulation`.

        Assigns (or re-assigns) an itinerary to every drone that currently
        lacks one or whose itinerary has become inoperative.  Drones that
        have already reached their destination are skipped.
        """
        for drone in list(self.__simulation.drones):
            # Skip drones that have already arrived.
            if drone.location == drone.destination:
                continue

            needs_itinerary = (
                drone.itinerary is None
                or not drone.itinerary.operative
            )
            if needs_itinerary:
                self.request_itinerary(drone)

    # ------------------------------------------------------------------
    # Dijkstra (internal)
    # ------------------------------------------------------------------

    def _dijkstra(
        self,
        origin: Hub,
        destination: Hub,
        current_turn: Turn,
    ) -> list[tuple[list[Hub], int]]:
        """
        Time-aware Dijkstra from *origin* to *destination*.

        Returns all discovered routes as ``(hub_path, arrival_turn)`` sorted
        ascending by arrival turn so ``request_itinerary`` can iterate through
        fallbacks in cost order.

        Implementation notes
        --------------------
        ``best_arrival[hub]`` records the lowest arrival turn *committed* for
        each hub.  A node popped from the heap is stale if its ``arrival_turn``
        is strictly greater than the recorded best; equal-cost paths are still
        processed so alternative routes of the same cost can be collected.

        Per-path cycle avoidance uses a ``frozenset[Hub]`` that travels with
        each node, avoiding the O(n) list-``in`` scan of the original
        implementation.
        """
        # best_arrival[hub] = lowest arrival_turn *settled* for that hub.
        best_arrival: dict[Hub, int] = {}
        # Collected complete paths, built in heap-pop order (already sorted).
        found: list[tuple[list[Hub], int]] = []

        heap: list[_Node] = []
        heapq.heappush(heap, _Node(
            arrival_turn=current_turn.value,
            hub=origin,
            visited=frozenset({origin}),
            path=[origin],
        ))

        while heap:
            node = heapq.heappop(heap)
            arr: int = node.arrival_turn
            hub: Hub = node.hub
            visited: frozenset[Hub] = node.visited
            path: list[Hub] = node.path

            # Prune stale entries: a *strictly* cheaper path was already settled.
            # We allow equal-cost entries through so we collect all optimal paths.
            if hub in best_arrival and best_arrival[hub] < arr:
                continue
            best_arrival[hub] = arr

            if hub == destination:
                found.append((path, arr))
                # Do NOT stop here: keep searching so we can collect fallback
                # paths with slightly higher cost (useful when the best path
                # fails to book).
                continue

            for connection in hub.connections:
                neighbour: Hub = connection.other_hub(hub)

                # Skip blocked hubs (impassable access level).
                if HubCost[neighbour.access] is None:
                    continue

                # Skip hubs already visited on this path (cycle prevention).
                if neighbour in visited:
                    continue

                # ── Simulate the temporal cost of this edge ────────────────
                #
                # Step 1: earliest turn a drone can *enter* the connection,
                #         checking both connection capacity and whether the
                #         destination hub will have a free slot in time.
                try:
                    # !THIS STATEMENT CAUSES INFINITE LOOP!!!!!!!
                    # TODO: FIX ERROR
                    conn_entry: Turn = self._safe_entry(
                        connection, Turn(arr), neighbour
                    )
                except TrafficError:
                    continue  # Connection or neighbour is unreachable.

                if conn_entry is None:
                    continue  # No free slot within _MAX_WAIT turns.

                # Step 2: earliest turn the drone can *exit* the connection
                #         into the neighbour hub (entry turn + traversal cost).
                try:
                    conn_exit: Turn = connection.get_next_available_exit(
                        conn_entry, neighbour
                    )
                except TrafficError:
                    continue

                # Step 3: earliest turn the neighbour hub itself has a free
                #         slot (it may be independently congested).
                try:
                    hub_entry: Turn = neighbour.get_next_available_entry(
                        conn_exit
                    )
                except TrafficError:
                    continue

                neighbour_arrival: int = hub_entry.value

                # Guard: skip if a cheaper or equal path to this neighbour
                # is already settled (equal is pruned for neighbours to avoid
                # exponential path explosion while still collecting all optimal
                # complete paths above).
                if (
                    neighbour in best_arrival
                    and best_arrival[neighbour] <= neighbour_arrival
                ):
                    continue

                heapq.heappush(heap, _Node(
                    arrival_turn=neighbour_arrival,
                    hub=neighbour,
                    visited=visited | {neighbour},
                    path=path + [neighbour],
                ))

        # The heap pops in ascending arrival_turn order, so `found` is already
        # sorted.  An explicit sort is a safety net against equal-cost ties.
        found.sort(key=lambda t: t[1])
        return found

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_entry(
        self,
        connection: "Connection",  # noqa: F821 – forward reference
        from_turn: Turn,
        destination: Hub,
    ) -> Turn | None:
        """
        Return the earliest turn >= *from_turn* at which *connection* can be
        entered toward *destination*, or ``None`` if no slot is found within
        ``_MAX_WAIT`` turns.

        This replaces the unbounded ``while True`` loop in
        ``Connection.get_next_available_entry`` with an explicit cap so the
        planner never hangs on a permanently saturated connection.
        """
        mov_cost = connection.get_movement_cost(destination)
        if mov_cost is None:
            return None  # Destination is blocked/impassable.

        limit = from_turn.value + _MAX_WAIT

        i = from_turn.value
        t = Turn(i)
        while i <= limit:
            t.value += 1
            # Check connection capacity at turn i.
            if connection.get_occupancy(t) >= connection.capacity:
                i += 1
                continue
            # Check whether the destination hub will be free at arrival.
            arrival = Turn(i + mov_cost)
            try:
                earliest_hub = destination.get_next_available_entry(arrival)
            except TrafficError:
                i += 1
                continue
            if earliest_hub.value == arrival.value:
                return Turn(i)
            # Hub won't be free exactly at arrival; jump to when it will.
            # This avoids scanning turns one-by-one when the hub is deeply
            # congested, since we already know the next free hub slot.
            gap = earliest_hub.value - arrival.value
            i += max(1, gap)

        return None  # Exceeded _MAX_WAIT; treat as unreachable.
