from typing import Any
from fastapi import UploadFile
from io import BytesIO
from glob import glob
from src.core.errors import ParseError
from src.models import Simulation, Hub, Connection, Drone
from src.utils.parser import parse_map
from tests.utils import assert_is_uuid
import pytest
import os


def assert_drone(drone: Any):
    assert isinstance(drone, Drone)
    assert_is_uuid(drone.id)
    assert (isinstance(drone.location, Hub) or
            isinstance(drone.location, Connection))
    assert drone in drone.location.drones


def assert_connection(connection: Any):
    assert isinstance(connection, Connection)
    assert_is_uuid(connection.id)
    assert connection.capacity > 0
    assert len(connection.hubs) == 2
    for h in connection.hubs:
        assert connection in h.connections


def assert_hub(hub: Any):
    assert isinstance(hub, Hub)
    assert_is_uuid(hub.id)
    assert "-" not in hub.name
    assert isinstance(hub.capacity, int)
    assert hub.capacity
    for c in hub.connections:
        assert hub in c.hubs


def assert_simulation(
    sim: Simulation,
    turn: int,
    hubs: int,
    connections: int,
    drones: int
):
    assert sim.turns == turn
    #  Hubs
    assert len(sim.hubs) == hubs
    for h in sim.hubs:
        assert_hub(h)
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
        for h in c.hubs:
            assert h in sim.hubs
    # Drones
    assert len(sim.drones) == drones
    for d in sim.drones:
        assert_drone(d)


# -----------------------
# Parse Map OK
# -----------------------


# Subject's maps
@pytest.mark.asyncio
async def test_parsing_ok_easy_01():
    with open("tests/maps/easy/01_linear_path.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=4,
        connections=3,
        drones=2
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_02():
    with open("tests/maps/easy/02_simple_fork.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=5,
        connections=5,
        drones=3
    )


@pytest.mark.asyncio
async def test_parsing_ok_easy_03():
    with open("tests/maps/easy/03_basic_capacity.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=4,
        connections=3,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_01():
    with open("tests/maps/medium/01_dead_end_trap.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=6,
        connections=5,
        drones=5
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_02():
    with open("tests/maps/medium/02_circular_loop.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=7,
        connections=7,
        drones=6
    )


@pytest.mark.asyncio
async def test_parsing_ok_medium_03():
    with open("tests/maps/medium/03_priority_puzzle.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_01():
    with open("tests/maps/hard/01_maze_nightmare.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=17,
        connections=20,
        drones=8
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_02():
    with open("tests/maps/hard/02_capacity_hell.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=15,
        connections=18,
        drones=12
    )


@pytest.mark.asyncio
async def test_parsing_ok_hard_03():
    with open("tests/maps/hard/03_ultimate_challenge.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=31,
        connections=37,
        drones=15
    )


@pytest.mark.asyncio
async def test_parsing_ok_challenger():
    with open("tests/maps/challenger/01_the_impossible_dream.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
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
async def test_parsing_ok_01():
    with open("tests/parsing/ok/parse_ok01.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_02():
    with open("tests/parsing/ok/parse_ok02.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_03():
    with open("tests/parsing/ok/parse_ok03.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


@pytest.mark.asyncio
async def test_parsing_ok_04():
    with open("tests/parsing/ok/parse_ok04.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=245,
        connections=355,
        drones=50
    )


@pytest.mark.asyncio
async def test_parsing_ok_05():
    with open("tests/parsing/ok/parse_ok05.txt", "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    s = await parse_map(file)
    assert_simulation(
        s,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


# -----------------------
# Create simulation ERROR
# -----------------------


def parse_error_files():
    errors = "tests/parsing/error"
    return glob(os.path.join(errors, '*.txt'))


@pytest.mark.parametrize("file_path", parse_error_files())
@pytest.mark.asyncio
async def test_parsing_error_batch(file_path: str):
    with open(file_path, "rb") as f:
        content = f.read()
    file = UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
    with pytest.raises(ParseError):
        await parse_map(file)
