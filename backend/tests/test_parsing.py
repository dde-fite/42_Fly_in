import pytest
import os
from typing import Any
from glob import glob
from pathlib import Path
from tests.utils import file_to_uploadfile
from src.core.errors import ParseError
from src.models import Simulation, Hub, Connection, Drone
from src.utils.parser import parse_map
from tests.utils import assert_uuid


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"
OWN_MAPS_DIR = Path(__file__).parent / "parsing"


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

# ─── Tests ───────────────────────────────────────────────────────────────────

# -----------------------
# Parse Map OK
# -----------------------


# Subject's maps
@pytest.mark.asyncio
async def test_parsing_ok_easy_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=["start", "waypoint1", "waypoint2", "goal"],
        connections=3,
        drones=2
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_02() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/02_simple_fork.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=["start", "junction", "path_a", "path_b", "goal"],
        connections=5,
        drones=3
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_03() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/03_basic_capacity.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=["start", "bottleneck", "wide_area", "goal"],
        connections=3,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/01_dead_end_trap.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "junction", "dead_end", "correct_path",
            "intermediate", "goal"
        ],
        connections=5,
        drones=5
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_02() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/02_circular_loop.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "loop_a", "loop_b", "loop_c", "loop_d",
            "exit_point", "goal"
        ],
        connections=7,
        drones=6
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_03() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/03_priority_puzzle.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "slow_path1", "slow_path2", "slow_path3",
            "fast_junction", "fast_path", "merge_point", "goal"
        ],
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/01_maze_nightmare.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "maze_a1", "maze_a2", "maze_b1", "maze_b2", "maze_c1",
            "maze_c2", "dead_end1", "dead_end2", "dead_end3", "trap_loop1",
            "trap_loop2", "bottleneck", "final_stretch1", "final_stretch2",
            "final_stretch3", "goal"
        ],
        connections=20,
        drones=8
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_02() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/02_capacity_hell.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "gate1", "gate2", "gate3", "waiting_area1",
            "waiting_area2", "waiting_area3", "restricted_tunnel1",
            "restricted_tunnel2", "restricted_tunnel3", "priority_bypass1",
            "priority_bypass2", "convergence", "final_bottleneck", "goal"
        ],
        connections=18,
        drones=12
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_03() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/03_ultimate_challenge.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=[
            "start", "dist_gate1", "dist_gate2", "dist_gate3", "maze_trap1",
            "maze_trap2", "maze_loop1", "maze_loop2", "maze_loop3",
            "maze_loop4", "maze_correct", "bottleneck1", "bottleneck2",
            "overflow1", "overflow2", "priority_hub", "priority_trap1",
            "priority_trap2", "priority_dead_end", "priority_correct",
            "conv_restricted1", "conv_restricted2", "conv_normal1",
            "conv_normal2", "conv_priority1", "conv_priority2", "final_merge",
            "final_gate1", "final_gate2", "final_gate3", "goal"
        ],
        connections=37,
        drones=15
    )


@pytest.mark.asyncio
async def test_parsing_ok_challenger() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "challenger/01_the_impossible_dream.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=54,
        connections=70,
        drones=25
    )


# Own maps
@pytest.mark.asyncio
async def test_parsing_ok_01() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok01.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_02() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok02.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_03() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok03.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_04() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok04.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=245,
        connections=355,
        drones=50
    )


@pytest.mark.asyncio
async def test_parsing_ok_05() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok05.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_06() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok06.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=5,
        connections=5,
        drones=3
    )
    assert s.origin.color == "rainbow"


@pytest.mark.asyncio
async def test_parsing_ok_07() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok07.txt")
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=5,
        connections=5,
        drones=3
    )
    assert s.origin.position.x == (
        523330231315344564654123513044240534564563412153045)
    assert s.origin.position.y == 56565

# -----------------------
# Create simulation ERROR
# -----------------------


def parse_error_files() -> list[str]:
    errors = OWN_MAPS_DIR / "error"
    return glob(os.path.join(errors, '*.txt'))


@pytest.mark.parametrize("file_path", parse_error_files())
@pytest.mark.asyncio
async def test_parsing_error_batch(file_path: str) -> None:
    file = file_to_uploadfile(file_path)
    with pytest.raises(ParseError):
        await parse_map(file)
