from __future__ import annotations
from typing import Any, Iterable, TYPE_CHECKING, cast
from src.core import TrafficError, SimulationConflict, logger, DEBUG
from .turn import Turn
from .hub import Hub
from .drone import Drone
from .connection import Connection
from .traffic_controller import TrafficController

if TYPE_CHECKING:
    from src.io import ParsedMap, ParsedConnection


class Simulation():

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

    def __init__(
            self,
            *,
            map: ParsedMap | None = None,

            hubs: Iterable[Hub] = [],
            origin: Hub | None = None,
            destination: Hub | None = None,
            connections: Iterable[Connection] = [],
            drones: Iterable[Drone] = [],
    ) -> None:
        self.turn: Turn = Turn(0)
        self.controller: TrafficController = TrafficController(self)
        self.hubs: set[Hub] = set()
        self.__origin: Hub | None = None
        self.__destination: Hub | None = None
        self.connections: set[Connection] = set()
        self.drones: set[Drone] = set()
        if map:
            self.__init_map(map)
        for h in hubs:
            is_origin = origin == h
            is_destination = destination == h
            self.add_hub(h, is_origin, is_destination)
        for c in connections:
            self.add_connection(c)
        for d in drones:
            self.add_drone(d)
        if logger.isEnabledFor(DEBUG):
            logger.debug(
                f"Simulation created: {self}"
            )

    def __init_map(self, map: ParsedMap) -> None:
        for h in map["hubs"]:
            h_obj = Hub(
                name=h["name"],
                position=h["position"],
                capacity=h["capacity"] if h["capacity"] is not None else 1,
                capacity_defined=(True if h["capacity"] is not None
                                  else False),
                access=h["access"],
                color=h["color"]
            )
            self.add_hub(
                h_obj,
                is_origin=h["is_origin"],
                is_destination=h["is_destination"]
            )
        for c in map["connection"]:
            c_obj = self.__make_connection_from_map(c)
            self.add_connection(c_obj)
        if map["nb_drones"]:
            for _i in range(map["nb_drones"]):
                self.make_drone()

    def __make_connection_from_map(
        self,
        data: ParsedConnection
    ) -> Connection:
        h1 = self.get_hub_by_name(data["hubs"][0])
        if not h1:
            raise SimulationConflict(
                f"Unknown hub '{data['hubs'][0]}' in connection: "
                f"'{data['hubs'][0]}'<->'{data['hubs'][1]}"
            )
        h2 = self.get_hub_by_name(data["hubs"][1])
        if not h2:
            raise SimulationConflict(
                f"Unknown hub '{data['hubs'][1]}' in connection: "
                f"'{data['hubs'][0]}'<->'{data['hubs'][1]}"
            )
        if h1 == h2:
            raise SimulationConflict(
                "Self connection not allowed: "
                f"{data['hubs'][0]}<->{data['hubs'][1]}"
            )
        params: dict[str, Any] = cast(dict[str, Any], data.copy())
        params["hubs"] = frozenset((h1, h2))
        params["capacity"] = (data["capacity"] if data["capacity"]
                              is not None else 1)
        con = Connection(**params)
        # In case of error, raises ValidationError
        return con

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def origin(self) -> Hub:
        if not self.__origin:
            raise SimulationConflict("Origin is not defined for simulation")
        return self.__origin

    @property
    def destination(self) -> Hub:
        if not self.__destination:
            raise SimulationConflict("Destination is not defined for simulation")
        return self.__destination

    def get_hub_by_name(self, hub_name: str) -> Hub | None:
        for h in self.hubs:
            if h.name == hub_name:
                return h
        return None

    def __update_capacity(self, quantity: int = 1) -> None:
        """
        Updates non capacity defined start/end hubs and checks if defined
        ones can support all drones.
        """
        # Origin
        if self.origin.capacity_defined:
            if len(self.drones) + quantity > self.origin.capacity:
                raise SimulationConflict(
                    "Origin capacity can not be less than drone quantity"
                )
        else:
            self.origin.capacity = len(self.drones) + quantity
        # Destination
        if self.destination.capacity_defined:
            if len(self.drones) + quantity > self.destination.capacity:
                raise SimulationConflict(
                    "Destination capacity can not be less than drone "
                    "quantity"
                )
        else:
            self.destination.capacity = len(self.drones) + quantity

    def add_drone(
        self,
        drone: Drone
    ) -> None:
        if drone in self.drones:
            raise SimulationConflict(
                "Drone already exist in this simulation"
            )
        if drone.origin not in self.hubs:
            raise SimulationConflict(
                "Drone origin is not part of this simulation"
            )
        if drone.destination not in self.hubs:
            raise SimulationConflict(
                "Drone destination is not part of this simulation"
            )
        drone.turn = self.turn
        self.drones.add(drone)

    def make_drone(
        self,
        origin: Hub | None = None,
        destination: Hub | None = None,
    ) -> Drone:
        """
        Spawn a new drone and add it to the simulation.

        Uses the simulation's default origin/destination if not provided.
        """
        self.__update_capacity()
        o = origin or self.origin
        d = destination or self.destination
        if o not in self.hubs:
            raise TrafficError(
                f"Origin hub '{o.name}' is not part of this simulation"
            )
        if d not in self.hubs:
            raise SimulationConflict(
                f"Destination hub '{d.name}' is not part of this simulation"
            )
        drone = Drone(origin=o, destination=d, turn=self.turn)
        # In case of error, raises ValidationError
        self.add_drone(drone)
        return drone

    def remove_drone(self, drone: Drone) -> None:
        """
        Remove a drone from the simulation, destroying its itinerary
        if any.
        """
        if drone.itinerary:
            drone.itinerary.destroy()
        self.drones.discard(drone)

    def add_hub(
        self,
        hub: Hub,
        is_origin: bool = False,
        is_destination: bool = False
    ) -> None:
        if ((is_origin and is_destination) or
           (hub == self.__origin and hub == self.__destination)):
            raise SimulationConflict(
                f"{hub.name} can not be origin and "
                "destination")
        for oh in self.hubs:
            if hub == oh:
                raise SimulationConflict("Duplicated hub names")
            if oh.position == hub.position:
                raise SimulationConflict(f"Conflict with hub '{oh.name}' and "
                                         f"'{oh.name}' coordinates")
        hub.turn = self.turn
        if is_origin:
            self.__origin = hub
        if is_destination:
            self.__destination = hub
        self.hubs.add(hub)

    def make_connection(
        self,
        hubs: tuple[str, str],
        **params: Any
    ) -> Connection:
        h1 = self.get_hub_by_name(hubs[0])
        if not h1:
            raise SimulationConflict(
                f"Unknown hub '{hubs[0]}' in connection: "
                f"'{hubs[0]}'<->'{hubs[1]}"
            )
        h2 = self.get_hub_by_name(hubs[1])
        if not h2:
            raise SimulationConflict(
                f"Unknown hub '{hubs[1]}' in connection: "
                f"'{hubs[0]}'<->'{hubs[1]}"
            )
        if h1 == h2:
            raise SimulationConflict(f"Self connection not allowed: {hubs[0]}<->{hubs[1]}")
        con = Connection(hubs=frozenset({h1, h2}), **params)
        # In case of error, raises ValidationError
        self.add_connection(con)
        return con

    def add_connection(self, connection: Connection) -> None:
        if connection in self.connections:
            raise SimulationConflict(
                "Connection already exist in this "
                "simulation"
            )
        for hub in connection.hubs:
            if hub not in self.hubs:
                raise SimulationConflict(f"Hub '{hub.name}' does not exist in "
                                         "simulation")
        connection.turn = self.turn
        self.connections.add(connection)

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
            6. Print drones moved
        """
        logger.debug(f"*********  BEGIN TURN {self.turn.value + 1} *********")
        drones_moved: list[Drone] = []

        # 1. Validate itineraries.
        for drone in list(self.drones):
            if drone.itinerary:
                try:
                    drone.itinerary.tick()
                except Exception:
                    pass  # ExpiredItinerary already destroys itself; continue.

        # 2. Route planning.
        self.controller.tick()

        # 5. Advance turn.
        self.turn.value += 1
        # 3. Drone movement.
        for drone in list(self.drones):
            if drone.tick():
                drones_moved.append(drone)

        # 4. Zone cleanup.
        for hub in self.hubs:
            hub.tick()
        for connection in self.connections:
            connection.tick()

        logger.debug(f"********* ENDED TURN {self.turn.value} *********")

        # 6. Print drones moved
        if drones_moved:
            for d in drones_moved:
                print(f"{d}-{d.location}", end=" ")
            print()

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
            f"connections={len(self.connections)}, "
            f"drones={len(self.drones)})"
        )
