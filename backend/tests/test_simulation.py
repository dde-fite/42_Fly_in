import pytest
import os
from typing import Any
from glob import glob
from pathlib import Path
from pydantic import ValidationError
from src.core.errors import ParseError, SimulationConflict, TrafficError
from src.models import Simulation, Hub, Connection, Drone, Itinerary
from src.models.vector import Vector
from src.io.parser import parse_map
from tests.utils import file_to_uploadfile, assert_uuid


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"
OWN_MAPS_DIR = Path(__file__).parent / "simulation"
PARSING__MAPS_DIR = Path(__file__).parent / "parsing"


def assert_drone(drone: Any) -> None:
    assert isinstance(drone, Drone)
    assert_uuid(drone.id)
    assert (isinstance(drone.location, Hub) or
            isinstance(drone.location, Connection))
    assert drone in drone.location.drones


def assert_connection(connection: Any) -> None:
    assert isinstance(connection, Connection)
    assert_uuid(connection.id)
    assert connection.capacity > 0
    assert len(connection.hubs) == 2
    for h in connection.hubs:
        assert connection in h.connections


def assert_hub(hub: Any) -> None:
    assert isinstance(hub, Hub)
    assert_uuid(hub.id)
    assert hub.name != ""
    assert "-" not in hub.name
    assert isinstance(hub.capacity, int)
    assert hub.capacity
    for c in hub.connections:
        assert hub in c.hubs


def assert_simulation(
    sim: Simulation,
    turn: int,
    hubs: int | list[str],
    connections: int,
    drones: int
) -> None:
    assert sim.turn.value == turn
    #  Hubs
    if isinstance(hubs, int):
        assert len(sim.hubs) == hubs
    else:
        assert len(sim.hubs) == len(hubs)
        for hub_name in hubs:
            assert sim.get_hub_by_name(hub_name)
        origin = sim.get_hub_by_name(hubs[0])
        destination = sim.get_hub_by_name(hubs[-1])
        assert origin
        assert destination
        assert origin.capacity >= drones
        assert destination.capacity >= drones
    for h in sim.hubs:
        assert_hub(h)
        assert h.turn == sim.turn
    assert_hub(sim.origin)
    assert sim.origin in sim.hubs
    assert sim.origin.capacity
    assert sim.origin.capacity >= len(sim.drones)
    assert_hub(sim.destination)
    assert sim.destination in sim.hubs
    # Connections
    assert len(sim.connections) == connections
    for c in sim.connections:
        assert_connection(c)
        assert c.turn == sim.turn
        for h in c.hubs:
            assert h in sim.hubs
    # Drones
    assert len(sim.drones) == drones
    for d in sim.drones:
        assert_drone(d)
        assert d.turn == sim.turn


# ─── Fixtures ────────────────────────────────────────────────────────────────

min_sim_type = tuple[Simulation, Hub, Hub]


@pytest.fixture
def minimal_simulation() -> min_sim_type:
    """
    Return a Simulation with exactly two hubs (origin + destination)
    and no connections or drones.
    """
    origin = Hub(name="origin", position=Vector(0, 0))
    destination = Hub(name="destination", position=Vector(1, 0))
    sim = Simulation()
    sim.add_hub(origin, is_origin=True)
    sim.add_hub(destination, is_destination=True)
    return sim, origin, destination


@pytest.fixture
def connected_simulation(
    minimal_simulation: min_sim_type
) -> tuple[Simulation, Hub, Hub, Connection]:
    """Simulation with origin→destination connected by one Connection."""
    sim, origin, destination = minimal_simulation
    conn = sim.make_connection(("origin", "destination"))
    return sim, origin, destination, conn


# ─── Construction ────────────────────────────────────────────────────────────


class TestSimulationInit:

    def test_empty_simulation_has_no_entities(self) -> None:
        sim = Simulation()
        assert sim.hubs == set()
        assert sim.connections == set()
        assert sim.drones == set()
        assert sim.turn.value == 0

    def test_linear_simulation(self) -> None:
        """
        Makes a linear simulation: A ── con_ab ── B ── con_bc ── C, with 1
        drone
        """
        hubs = {
            "A": Hub(name="A", position=Vector(x=0, y=0)),
            "B": Hub(name="B", position=Vector(x=1, y=0)),
            "C": Hub(name="C", position=Vector(x=2, y=0))
        }
        connections = {
            "AB": Connection(hubs=frozenset({hubs["A"], hubs["B"]})),
            "BC": Connection(hubs=frozenset({hubs["B"], hubs["C"]}))
        }
        drones = [
            Drone(origin=hubs["A"], destination=hubs["C"])
        ]
        sim = Simulation(
            hubs=hubs.values(),
            origin=hubs["A"],
            destination=hubs["C"],
            connections=connections.values(),
            drones=drones
        )
        assert_simulation(
            sim=sim,
            turn=0,
            hubs=["A", "B", "C"],
            connections=2,
            drones=1
        )

    def test_origin_raises_when_not_set(self) -> None:
        sim = Simulation()
        with pytest.raises(SimulationConflict):
            _ = sim.origin

    def test_destination_raises_when_not_set(self) -> None:
        sim = Simulation()
        with pytest.raises(SimulationConflict):
            _ = sim.destination

# ─── Construction from ParsedMap ─────────────────────────────────────────────


class TestSimulationFromMap:

    # Subject's maps
    @pytest.mark.asyncio
    async def test_parsing_ok_easy_01(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "easy/01_linear_path.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=["start", "waypoint1", "waypoint2", "goal"],
            connections=3,
            drones=2
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_easy_02(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "easy/02_simple_fork.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=["start", "junction", "path_a", "path_b", "goal"],
            connections=5,
            drones=3
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_easy_03(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "easy/03_basic_capacity.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=["start", "bottleneck", "wide_area", "goal"],
            connections=3,
            drones=4
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_medium_01(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "medium/01_dead_end_trap.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "junction", "dead_end", "correct_path",
                "intermediate", "goal"
            ],
            connections=5,
            drones=5
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_medium_02(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "medium/02_circular_loop.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "loop_a", "loop_b", "loop_c", "loop_d",
                "exit_point", "goal"
            ],
            connections=7,
            drones=6
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_medium_03(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "medium/03_priority_puzzle.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "slow_path1", "slow_path2",
                "fast_junction", "fast_path", "merge_point", "goal"
            ],
            connections=7,
            drones=4
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_hard_01(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "hard/01_maze_nightmare.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "maze_a1", "maze_a2", "maze_b1", "maze_b2", "maze_c1",
                "maze_c2", "dead_end1", "dead_end2", "dead_end3", "trap_loop1",
                "trap_loop2", "bottleneck", "final_stretch1", "final_stretch2",
                "final_stretch3", "goal"
            ],
            connections=22,
            drones=8
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_hard_02(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "hard/02_capacity_hell.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "gate1", "gate2", "gate3", "waiting_area1",
                "waiting_area2", "waiting_area3", "restricted_tunnel1",
                "restricted_tunnel2", "restricted_tunnel3", "priority_bypass1",
                "priority_bypass2", "convergence", "final_bottleneck", "goal"
            ],
            connections=21,
            drones=12
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_hard_03(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "hard/03_ultimate_challenge.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=[
                "start", "dist_gate1", "dist_gate2", "dist_gate3",
                "maze_trap1", "maze_trap2", "maze_loop1", "maze_loop2",
                "maze_loop3", "maze_loop4", "maze_correct", "bottleneck1",
                "bottleneck2", "overflow1", "overflow2", "priority_hub",
                "priority_trap1", "priority_trap2", "priority_dead_end",
                "priority_correct", "conv_restricted1", "conv_restricted2",
                "conv_normal1", "conv_normal2", "conv_priority1",
                "conv_priority2", "final_merge", "final_gate1",
                "final_gate2", "final_gate3", "goal"
            ],
            connections=37,
            drones=15
        )

    @pytest.mark.asyncio
    async def test_parsing_ok_challenger(self) -> None:
        file = file_to_uploadfile(
            SUBJECT_MAPS_DIR / "challenger/01_the_impossible_dream.txt"
        )
        map = await parse_map(file)
        sim = Simulation(map=map)
        assert_simulation(
            sim,
            turn=0,
            hubs=54,
            connections=70,
            drones=25
        )

    @staticmethod
    def simulation_error_files() -> list[str]:
        errors = OWN_MAPS_DIR / "error"
        return glob(os.path.join(errors, '*.txt'))

    @pytest.mark.parametrize("file_path", simulation_error_files())
    @pytest.mark.asyncio
    async def test_simulation_error_batch(self, file_path: str) -> None:
        file = file_to_uploadfile(file_path)
        with pytest.raises((ValidationError, SimulationConflict, ParseError)):
            map = await parse_map(file)
            Simulation(map=map)


# ─── add_hub ─────────────────────────────────────────────────────────────────


class TestAddHub:

    def test_add_hub_registers_in_hubs_set(self) -> None:
        sim = Simulation()
        hub = Hub(name="alpha", position=Vector(0, 0))
        sim.add_hub(hub)
        assert hub in sim.hubs
        assert_hub(hub)
        with pytest.raises(SimulationConflict):
            sim.origin
        with pytest.raises(SimulationConflict):
            sim.destination
        assert hub.position.x == 0
        assert hub.position.y == 0
        assert hub.turn == sim.turn

    def test_add_hub_as_origin_sets_origin(self) -> None:
        sim = Simulation()
        hub = Hub(name="start", position=Vector(0, 0))
        sim.add_hub(hub, is_origin=True)
        assert hub in sim.hubs
        assert_hub(hub)
        assert sim.origin == hub
        with pytest.raises(SimulationConflict):
            sim.destination
        assert hub.position.x == 0
        assert hub.position.y == 0
        assert hub.turn == sim.turn

    def test_add_hub_as_destination_sets_destination(self) -> None:
        sim = Simulation()
        hub = Hub(name="end", position=Vector(0, 0))
        sim.add_hub(hub, is_destination=True)
        assert hub in sim.hubs
        assert_hub(hub)
        with pytest.raises(SimulationConflict):
            sim.origin
        assert sim.destination == hub
        assert hub.position.x == 0
        assert hub.position.y == 0
        assert hub.turn == sim.turn

    def test_duplicate_hub_raises_conflict(self) -> None:
        sim = Simulation()
        hub = Hub(name="alpha", position=Vector(0, 0))
        sim.add_hub(hub)
        with pytest.raises(SimulationConflict):
            sim.add_hub(hub)

    def test_duplicate_hub_name_raises_conflict(self) -> None:
        sim = Simulation()
        sim.add_hub(Hub(name="alpha", position=Vector(0, 0)))
        with pytest.raises(SimulationConflict):
            sim.add_hub(Hub(name="alpha", position=Vector(1, 0)))

    def test_duplicate_position_raises_conflict(self) -> None:
        sim = Simulation()
        sim.add_hub(Hub(name="alpha", position=Vector(0, 0)))
        with pytest.raises(SimulationConflict):
            sim.add_hub(Hub(name="beta", position=Vector(0, 0)))

    def test_origin_and_destination_same_hub_raises_conflict(self) -> None:
        sim = Simulation()
        hub = Hub(name="both", position=Vector(0, 0))
        with pytest.raises(SimulationConflict):
            sim.add_hub(hub, is_origin=True, is_destination=True)


# ─── make_connection / add_connection ────────────────────────────────────────


class TestConnections:

    def test_make_connection_registers_in_connections(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, origin, destination = minimal_simulation
        conn = sim.make_connection(("origin", "destination"))
        assert conn in sim.connections

    def test_make_connection_registers_in_both_hubs(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, origin, destination = minimal_simulation
        conn = sim.make_connection(("origin", "destination"))
        assert conn in origin.connections
        assert conn in destination.connections

    def test_make_connection_unknown_hub_raises(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        with pytest.raises(SimulationConflict):
            sim.make_connection(("origin", "nonexistent"))

    def test_make_connection_self_loop_raises(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        with pytest.raises(SimulationConflict):
            sim.make_connection(("origin", "origin"))

    def test_add_connection_duplicate_raises_conflict(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, origin, destination = minimal_simulation
        conn = sim.make_connection(("origin", "destination"))
        with pytest.raises(SimulationConflict):
            sim.add_connection(conn)

    def test_add_connection_hub_not_in_simulation_raises_conflict(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        orphan = Hub(name="orphan", position=Vector(99, 99))
        other = Hub(name="other", position=Vector(98, 98))
        conn = Connection(hubs=frozenset({orphan, other}), capacity=1)
        with pytest.raises(SimulationConflict):
            sim.add_connection(conn)

    def test_connection_shares_turn_object(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        conn = sim.make_connection(("origin", "destination"))
        assert conn.turn is sim.turn


# ─── add_drone / remove_drone ────────────────────────────────────────────────


class TestDrones:

    def test_make_drone_default(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, origin, destination = minimal_simulation
        drone = sim.make_drone()
        assert drone.location == origin
        assert drone.destination == destination
        assert drone in sim.drones
        assert drone.turn is sim.turn
        assert_drone(drone)

    def test_add_drone_custom_origin_outside_sim_raises_traffic_error(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        alien_hub = Hub(name="alien", position=Vector(50, 50))
        dest = sim.destination
        with pytest.raises(TrafficError):
            sim.make_drone(origin=alien_hub, destination=dest)

    def test_add_drone_custom_destination_outside_sim_raises_conflict(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        alien_hub = Hub(name="alien", position=Vector(50, 50))
        with pytest.raises(SimulationConflict):
            sim.make_drone(destination=alien_hub)

    def test_add_drone_exceeding_origin_capacity_raises_conflict(self) -> None:
        origin = Hub(name="start", position=Vector(0, 0), capacity=1,
                     capacity_defined=True)
        destination = Hub(name="end", position=Vector(1, 0), capacity=10,
                          capacity_defined=True)
        # Force capacity_defined so __update_capacity enforces the limit
        sim = Simulation()
        sim.add_hub(origin, is_origin=True)
        sim.add_hub(destination, is_destination=True)
        sim.make_drone()  # fills the single slot
        with pytest.raises(SimulationConflict):
            sim.make_drone()

    def test_remove_drone_removes_from_drones_set(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        drone = sim.make_drone()
        sim.remove_drone(drone)
        assert drone not in sim.drones

    def test_remove_nonexistent_drone_is_a_noop(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        # remove_drone uses discard; passing something not present must not
        # raise
        drone = Drone(
            origin=sim.origin, destination=sim.destination, turn=sim.turn)
        sim.remove_drone(drone)


# ─── get_hub_by_name ─────────────────────────────────────────────────────────


class TestGetHubByName:

    def test_returns_correct_hub(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, origin, _ = minimal_simulation
        assert sim.get_hub_by_name("origin") is origin

    def test_returns_none_for_unknown_name(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        assert sim.get_hub_by_name("ghost") is None


# ─── tick / run ──────────────────────────────────────────────────────────────


class TestTickAndRun:

    def test_tick_advances_turn(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        sim.make_connection(("origin", "destination"))
        sim.make_drone()
        sim.tick()
        assert sim.turn.value == 1

    def test_multiple_ticks_advance_turn_correctly(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        sim.make_connection(("origin", "destination"))
        sim.make_drone()
        for _ in range(5):
            sim.tick()
        assert sim.turn.value == 5

    def test_run_returns_zero_when_no_drones(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        """With no drones, all_done is vacuously True → run returns 0."""
        sim, _, _ = minimal_simulation
        result = sim.run(max_turns=100)
        assert result == 0

    def test_run_respects_max_turns(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        """
        If drones never reach destination, run() must return max_turns
        (no infinite loop).
        """
        sim, _, _ = minimal_simulation
        sim.make_connection(("origin", "destination"))
        sim.make_drone()
        result = sim.run(max_turns=10)
        assert result <= 10

    def test_turn_shared_after_tick(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        """After a tick, all entities must still reference the same turn."""
        sim, _, _ = minimal_simulation
        sim.make_connection(("origin", "destination"))
        drone = sim.make_drone()
        sim.tick()
        assert drone.turn is sim.turn
        for hub in sim.hubs:
            assert hub.turn is sim.turn


# ─── status / repr ───────────────────────────────────────────────────────────


class TestDiagnostics:

    def test_status_contains_expected_keys(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        sim.make_drone()
        s = sim.status()
        assert "turn" in s
        assert "drones" in s
        assert "hub_occupancy" in s

    def test_status_turn_matches_simulation_turn(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        sim.make_connection(("origin", "destination"))
        sim.make_drone()
        sim.tick()
        assert sim.status()["turn"] == 1

    def test_repr_contains_turn_hubs_drones(
        self,
        minimal_simulation: min_sim_type
    ) -> None:
        sim, _, _ = minimal_simulation
        r = repr(sim)
        assert "turn=" in r
        assert "hubs=" in r
        assert "drones=" in r


# ─── Itinerary edge cases ────────────────────────────────────────────────────


class TestItineraryEdgeCases:

    @pytest.fixture
    def two_hub_sim(self) -> Simulation:
        sim = Simulation()
        a = Hub(name="A", position=Vector(0, 0))
        b = Hub(name="B", position=Vector(1, 0))
        sim.add_hub(a, is_origin=True)
        sim.add_hub(b, is_destination=True)
        Connection(hubs=frozenset({a, b}), turn=sim.turn)
        return sim

    def test_itinerary_requires_at_least_one_hub(
        self, two_hub_sim: Simulation
    ) -> None:
        sim = two_hub_sim
        drone = sim.make_drone()
        with pytest.raises(TrafficError):
            Itinerary(drone=drone, hubs=[], turn=sim.turn)

    def test_itinerary_raises_if_drone_already_has_one(
        self, two_hub_sim: Simulation
    ) -> None:
        sim = two_hub_sim
        drone = sim.make_drone()
        Itinerary(
            drone=drone, hubs=[sim.origin, sim.destination], turn=sim.turn
        )
        with pytest.raises(TrafficError):
            Itinerary(
                drone=drone,
                hubs=[sim.origin, sim.destination],
                turn=sim.turn,
            )

    def test_itinerary_raises_when_no_connection_between_hubs(
        self, two_hub_sim: Simulation
    ) -> None:
        sim = two_hub_sim
        # Add a third hub with no connection to A or B
        c = Hub(name="C", position=Vector(2, 0))
        sim.add_hub(c)
        drone = sim.make_drone()
        with pytest.raises(TrafficError):
            Itinerary(drone=drone, hubs=[sim.origin, c], turn=sim.turn)

    def test_itinerary_tick_is_noop_when_not_operative(
        self, two_hub_sim: Simulation
    ) -> None:
        sim = two_hub_sim
        drone = sim.make_drone()
        it = Itinerary(
            drone=drone, hubs=[sim.origin, sim.destination], turn=sim.turn
        )
        it.destroy()
        assert not it.operative
        it.tick()  # must not raise

    def test_itinerary_expired_itinerary_raises(
        self, two_hub_sim: Simulation
    ) -> None:
        from src.core.errors import ExpiredItinerary
        sim = two_hub_sim
        drone = sim.make_drone()
        it = Itinerary(
            drone=drone, hubs=[sim.origin, sim.destination], turn=sim.turn
        )
        with pytest.raises(ExpiredItinerary):
            it.expired_itinerary()

    def test_itinerary_destroy_detaches_drone(
        self, two_hub_sim: Simulation
    ) -> None:
        sim = two_hub_sim
        drone = sim.make_drone()
        it = Itinerary(
            drone=drone, hubs=[sim.origin, sim.destination], turn=sim.turn
        )
        assert drone.itinerary is it
        it.destroy()
        assert drone.itinerary is None
        assert not it.operative
