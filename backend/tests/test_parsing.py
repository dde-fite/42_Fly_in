import pytest
import os
from glob import glob
from pathlib import Path
from tests.utils import file_to_uploadfile
from src.core.errors import ParseError
from src.io import ParsedMap, ParsedConnection, ParsedHub
from src.io.parser import parse_map


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"
OWN_MAPS_DIR = Path(__file__).parent / "parsing"


def assert_hub(hub: ParsedHub) -> None:
    assert isinstance(hub, dict)
    assert isinstance(hub["name"], str)
    assert "-" not in hub["name"]
    # capacity may be None (parser leaves it None when not specified in file)
    if hub["capacity"] is not None:
        assert isinstance(hub["capacity"], int)
        assert hub["capacity"] > 0
    assert isinstance(hub["is_origin"], bool)
    assert isinstance(hub["is_destination"], bool)


def assert_connection(connection: ParsedConnection) -> None:
    assert isinstance(connection, dict)
    assert len(connection["hubs"]) == 2
    for hub_name in connection["hubs"]:
        assert isinstance(hub_name, str)
        assert hub_name  # non-empty
    if connection["capacity"] is not None:
        assert isinstance(connection["capacity"], int)
        assert connection["capacity"] > 0


def get_origin(parsed: ParsedMap) -> ParsedHub | None:
    """Return the hub marked as origin, or None if not present."""
    origins = [h for h in parsed["hubs"] if h["is_origin"]]
    return origins[0] if origins else None


def get_destination(parsed: ParsedMap) -> ParsedHub | None:
    """Return the hub marked as destination, or None if not present."""
    destinations = [h for h in parsed["hubs"] if h["is_destination"]]
    return destinations[0] if destinations else None


def get_hub_by_name(parsed: ParsedMap, name: str) -> ParsedHub | None:
    for h in parsed["hubs"]:
        if h["name"] == name:
            return h
    return None


def assert_map(
    parsed: ParsedMap,
    hubs: int | list[str],
    connections: int,
    drones: int,
) -> None:
    # Drones
    assert parsed["nb_drones"] == drones
    # Hubs
    if isinstance(hubs, int):
        assert len(parsed["hubs"]) == hubs
    else:
        assert len(parsed["hubs"]) == len(hubs)
        for hub_name in hubs:
            assert get_hub_by_name(parsed, hub_name) is not None, (
                f"Hub '{hub_name}' not found in parsed map"
            )
        # Convention: first name == origin, last name == destination
        origin_name, destination_name = hubs[0], hubs[-1]
        origin = get_hub_by_name(parsed, origin_name)
        destination = get_hub_by_name(parsed, destination_name)
        assert origin is not None
        assert destination is not None
        assert origin["is_origin"], (
            f"Hub '{origin_name}' should be marked as origin"
        )
        assert destination["is_destination"], (
            f"Hub '{destination_name}' should be marked as destination"
        )
    for h in parsed["hubs"]:
        assert_hub(h)
    # There must be exactly one origin and one destination
    assert get_origin(parsed) is not None, "No origin hub found"
    assert get_destination(parsed) is not None, "No destination hub found"
    # Connections
    assert len(parsed["connection"]) == connections
    for c in parsed["connection"]:
        assert_connection(c)
    # Every connection references hub names that exist in the hub list
    hub_names = {h["name"] for h in parsed["hubs"]}
    for c in parsed["connection"]:
        for hub_name in c["hubs"]:
            assert hub_name in hub_names, (
                f"Connection references unknown hub '{hub_name}'"
            )

# ─── Tests ───────────────────────────────────────────────────────────────────

# -----------------------
# Parse Map OK
# -----------------------


# Subject's maps
@pytest.mark.asyncio
async def test_parsing_ok_easy_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=["start", "waypoint1", "waypoint2", "goal"],
        connections=3,
        drones=2
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_02() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/02_simple_fork.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=["start", "junction", "path_a", "path_b", "goal"],
        connections=5,
        drones=3
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_03() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/03_basic_capacity.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=["start", "bottleneck", "wide_area", "goal"],
        connections=3,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/01_dead_end_trap.txt")
    s = await parse_map(file)
    assert_map(
        s,
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
    assert_map(
        s,
        hubs=[
            "start", "loop_a", "loop_b", "loop_c", "loop_d",
            "exit_point", "goal"
        ],
        connections=7,
        drones=6
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_03() -> None:
    file = file_to_uploadfile(
        SUBJECT_MAPS_DIR / "medium/03_priority_puzzle.txt"
    )
    s = await parse_map(file)
    assert_map(
        s,
        hubs=[
            "start", "slow_path1", "slow_path2", "fast_junction", "fast_path",
            "merge_point", "goal"
        ],
        connections=7,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/01_maze_nightmare.txt")
    s = await parse_map(file)
    assert_map(
        s,
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
async def test_parsing_ok_hard_02() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/02_capacity_hell.txt")
    s = await parse_map(file)
    assert_map(
        s,
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
async def test_parsing_ok_hard_03() -> None:
    file = file_to_uploadfile(
        SUBJECT_MAPS_DIR / "hard/03_ultimate_challenge.txt"
    )
    s = await parse_map(file)
    assert_map(
        s,
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
    file = file_to_uploadfile(
        SUBJECT_MAPS_DIR / "challenger/01_the_impossible_dream.txt"
    )
    s = await parse_map(file)
    assert_map(
        s,
        hubs=54,
        connections=70,
        drones=25
    )


# Own maps
@pytest.mark.asyncio
async def test_parsing_ok_01() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok01.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_02() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok02.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_03() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok03.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_04() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok04.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=245,
        connections=355,
        drones=50
    )


@pytest.mark.asyncio
async def test_parsing_ok_05() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok05.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_06() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok06.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=5,
        connections=5,
        drones=3
    )
    assert s["hubs"][0]["color"] == "rainbow"


@pytest.mark.asyncio
async def test_parsing_ok_07() -> None:
    file = file_to_uploadfile(OWN_MAPS_DIR / "ok/parse_ok07.txt")
    s = await parse_map(file)
    assert_map(
        s,
        hubs=5,
        connections=5,
        drones=3
    )
    assert s["hubs"][0]["position"].x == (
        523330231315344564654123513044240534564563412153045)
    assert s["hubs"][0]["position"].y == 56565

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
