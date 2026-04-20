from typing import Any
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from glob import glob
from random import choice, randint
from src.api.routes import router
from tests.utils import assert_is_uuid
import pytest
import os
import secrets
import string


app = FastAPI()
app.include_router(router, prefix="/api")

client = TestClient(app)


def assert_simulation_response(
    data: dict[str, Any],
    turn: int,
    hubs: int,
    connections: int,
    drones: int
) -> None:
    assert data["turns"] == turn
    assert len(data["hubs"]) == hubs
    for hub in data["hubs"]:
        assert_is_uuid(hub)
    assert_is_uuid(data["origin"])
    assert_is_uuid(data["destination"])
    assert len(data["connections"]) == connections
    for con in data["connections"]:
        assert_is_uuid(con)
    assert len(data["drones"]) == drones
    for drone in data["drones"]:
        assert_is_uuid(drone)


def random_string(length: int = randint(1, 50)) -> str:
    chars = string.ascii_letters + string.digits + "+/="
    return ''.join(choice(chars) for _ in range(length))

# -----------------------
# Create simulation OK strict
# -----------------------


# Subject's maps
def test_create_simulation_ok_easy_01() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=4,
        connections=3,
        drones=2
    )


def test_create_simulation_ok_easy_02() -> None:
    with open("tests/maps/easy/02_simple_fork.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=5,
        connections=5,
        drones=3
    )


def test_create_simulation_ok_easy_03() -> None:
    with open("tests/maps/easy/03_basic_capacity.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=4,
        connections=3,
        drones=4
    )


def test_create_simulation_ok_challenger() -> None:
    with open(
        "tests/maps/challenger/01_the_impossible_dream.txt"
    ) as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=54,
        connections=70,
        drones=25
    )


# ok tests
def test_create_simulation_ok_01() -> None:
    with open("tests/parsing/ok/parse_ok01.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


def test_create_simulation_ok_02() -> None:
    with open("tests/parsing/ok/parse_ok02.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )
    assert res.status_code == 200
    data = res.json()
    assert_simulation_response(
        data,
        turn=0,
        hubs=8,
        connections=8,
        drones=4
    )


# -----------------------
# Create simulation ERROR
# -----------------------

# Parsing Errors
def parse_error_files() -> list[str]:
    errors = "tests/parsing/error"
    return glob(os.path.join(errors, '*.txt'))


@pytest.mark.parametrize("file_path", parse_error_files())
def test_create_simulation_parse_error_batch(file_path: str) -> None:
    with open(file_path) as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32)},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 400
    data = res.json()
    assert "detail" in data


# Bad tokens
def test_create_simulation_bad_token_01() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": "0"},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_02() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(32) + "="},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_03() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(31)},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_04() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(16)},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_05() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": "000000000000000000000000000"},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_06() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_07() -> None:
    with open("tests/maps/easy/01_linear_path.txt") as file:
        map = file.read()

    for _ in range(100):
        res = client.post(
            "/api/simulation",
            params={"token": random_string()},
            files={"file": ("file", map, "text/plain")}
        )
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data


# Repeated tokens
def test_create_simulation_repeated_token_01() -> None:
    token = secrets.token_urlsafe(32)
    with open("tests/maps/easy/01_linear_path.txt") as file:
        map = file.read()

    res = client.post(
        "/api/simulation",
        params={"token": token},
        files={"file": ("file", map, "text/plain")}
    )
    assert res.status_code == 200

    res = client.post(
        "/api/simulation",
        params={"token": token},
        files={"file": ("file", map, "text/plain")}
    )

    assert res.status_code == 400
    data = res.json()
    assert "detail" in data


def test_create_simulation_repeated_token_02() -> None:
    token = secrets.token_urlsafe(32)
    with open("tests/maps/easy/01_linear_path.txt") as file:
        map = file.read()
    res = client.post(
            "/api/simulation",
            params={"token": token},
            files={"file": ("file", map, "text/plain")}
        )
    assert res.status_code == 200

    for _i in range(100):
        res = client.post(
            "/api/simulation",
            params={"token": token},
            files={"file": ("file", map, "text/plain")}
        )
        assert res.status_code == 400
        data = res.json()
        assert "detail" in data


# # -----------------------
# # SIMULATION - GET
# # -----------------------
# @patch("src.api.fetch_simulation")
# def test_get_simulation_ok(mock_fetch):
#     mock_fetch.return_value = {"token": "abc"}

#     res = client.get("/api/simulation", params={"token": "abc"})
#     assert res.status_code == 200


# @patch("src.api.fetch_simulation")
# def test_get_simulation_not_found(mock_fetch):
#     from src.core import SimulationNotFound
#     mock_fetch.side_effect = SimulationNotFound()

#     res = client.get("/api/simulation", params={"token": "abc"})
#     assert res.status_code == 404


# # -----------------------
# # HUB / DRONE / CONNECTION
# # -----------------------
# @patch("src.api.fetch_hub")
# def test_get_hub(mock_fetch):
#     mock_fetch.return_value = {"id": "hub1"}

#     res = client.get("/api/hub", params={"token": "abc", "id": "hub1"})
#     assert res.status_code == 200


# @patch("src.api.fetch_drone")
# def test_get_drone(mock_fetch):
#     mock_fetch.return_value = {"id": "drone1"}

#     res = client.get("/api/drone", params={"token": "abc", "id": "drone1"})
#     assert res.status_code == 200


# @patch("src.api.fetch_connection")
# def test_get_connection(mock_fetch):
#     mock_fetch.return_value = {"id": "conn1"}

#     res = client.get("/api/connection", params={"token": "abc", "id": "conn1"})
#     assert res.status_code == 200


# # -----------------------
# # STEP SIMULATION
# # -----------------------
# @patch("src.api.execute_turn")
# def test_step_simulation(mock_exec):
#     mock_exec.return_value = {"token": "abc", "step": 1}

#     res = client.post(
#         "/api/simulation/step",
#         params={"token": "abc", "steps": 1}
#     )

#     assert res.status_code == 200


# @patch("src.api.execute_turn")
# def test_step_simulation_not_found(mock_exec):
#     from src.core import SimulationNotFound
#     mock_exec.side_effect = SimulationNotFound()

#     res = client.post(
#         "/api/simulation/step",
#         params={"token": "abc", "steps": 1}
#     )

#     assert res.status_code == 404
