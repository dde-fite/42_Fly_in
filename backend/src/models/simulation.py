from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, model_validator
from src.core.errors import TrafficError
from .turn import Turn
from .hub import Hub
from .drone import Drone
from .connection import Connection
from .traffic_controller import TrafficController


class Simulation(BaseModel):

    """
    Top-level container that owns all simulation entities and drives the
    turn-by-turn execution loop.

    Attributes:
        turn (Turn): Shared mutable Turn object.  All entities reference this
                  same instance so advancing it here propagates everywhere.
        hubs (set[Hub]): All hubs in the airspace graph.
        origin (Hub): Default spawn hub (used when adding drones without a custom origin).
        destination (Hub): Default destination hub.
        connections (set[Connection]): All connections in the airspace graph.
        drones (set[Drone]): Active drones being simulated.
        controller (TrafficController): Traffic controller instance responsible for route planning.
    """

    turn: Turn
    hubs: set[Hub]
    origin: Hub
    destination: Hub
    connections: set[Connection]
    drones: set[Drone] = Field(default_factory=set[Drone])
    controller: TrafficController = Field(default_factory=TrafficController)

    model_config = {"arbitrary_types_allowed": True}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def validate_graph(self) -> Simulation:
        if self.origin not in self.hubs:
            raise ValueError("origin must be a member of hubs")
        if self.destination not in self.hubs:
            raise ValueError("destination must be a member of hubs")
        for connection in self.connections:
            for hub in connection.hubs:
                if hub not in self.hubs:
                    raise ValueError(
                        f"Connection references hub '{hub.name}' "
                        "which is not in the simulation's hub set"
                    )
        return self

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_drone(
        self,
        origin: Hub | None = None,
        destination: Hub | None = None,
    ) -> Drone:
        """
        Spawn a new drone and add it to the simulation.

        Uses the simulation's default origin/destination if not provided.
        """
        o = origin or self.origin
        d = destination or self.destination
        if o not in self.hubs:
            raise TrafficError(f"Origin hub '{o.name}' is not part of this simulation")
        if d not in self.hubs:
            raise TrafficError(f"Destination hub '{d.name}' is not part of this simulation")

        drone = Drone(origin=o, destination=d, turn=self.turn)
        self.drones.add(drone)
        return drone

    def remove_drone(self, drone: Drone) -> None:
        """Remove a drone from the simulation, destroying its itinerary if any."""
        if drone.itinerary:
            drone.itinerary.destroy()
        self.drones.discard(drone)

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """
        Advance the simulation by one turn.

        Order of operations per turn:
            1. TrafficController assigns itineraries to drones that lack one.
            2. Each Itinerary validates itself (expiry / stale bookings).
            3. Each Drone attempts to move (request_exit on its current zone).
            4. Each TransitableZone purges expired bookings.
            5. The global turn counter is incremented.
        """
        # 1. Route planning.
        self.controller.tick(self)

        # 2. Validate itineraries.
        for drone in list(self.drones):
            if drone.itinerary:
                try:
                    drone.itinerary.tick()
                except Exception:
                    pass  # ExpiredItinerary already destroys itself; continue.

        # 3. Drone movement.
        for drone in list(self.drones):
            drone.tick()

        # 4. Zone cleanup.
        for hub in self.hubs:
            hub.tick()
        for connection in self.connections:
            connection.tick()

        # 5. Advance turn.
        self.turn.value += 1

    def run(self, max_turns: int = 1000) -> int:
        """
        Run the simulation until all drones reach their destination or
        *max_turns* is exceeded.

        Returns the number of turns executed.
        """
        for t in range(max_turns):
            all_done = all(
                drone.location == drone.destination for drone in self.drones
            )
            if all_done:
                return t
            self.tick()
        return max_turns

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Return a snapshot of the current simulation state for debugging."""
        return {
            "turn": self.turn.value,
            "drones": [
                {
                    "id": str(drone.id),
                    "location": getattr(drone.location, "name", str(drone.location)),
                    "destination": drone.destination.name,
                    "has_itinerary": drone.itinerary is not None,
                    "arrived": drone.location == drone.destination,
                }
                for drone in self.drones
            ],
            "hub_occupancy": {
                hub.name: len(hub.drones) for hub in self.hubs
            },
        }

    def __repr__(self) -> str:
        return (
            f"Simulation(turn={self.turn.value}, "
            f"hubs={len(self.hubs)}, "
            f"drones={len(self.drones)})"
        )
