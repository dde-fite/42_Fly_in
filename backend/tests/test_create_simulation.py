import pytest
import os
import secrets
import string
from typing import Any
from glob import glob
from random import choice, randint
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.routes import router
from tests.utils import assert_uuid


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"
OWN_MAPS_DIR = Path(__file__).parent / "parsing"

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
    assert data["turn"] == turn
    assert len(data["hubs"]) == hubs
    for hub in data["hubs"]:
        assert_uuid(hub)
    assert_uuid(data["origin"])
    assert_uuid(data["destination"])
    assert len(data["connections"]) == connections
    for con in data["connections"]:
        assert_uuid(con)
    assert len(data["drones"]) == drones
    for drone in data["drones"]:
        assert_uuid(drone)


def random_string(length: int = randint(1, 50)) -> str:
    chars = string.ascii_letters + string.digits + "+/="
    return ''.join(choice(chars) for _ in range(length))

# ─── Tests ───────────────────────────────────────────────────────────────────

# -----------------------
# Create simulation OK strict
# -----------------------


# Subject's maps
def test_create_simulation_ok_easy_01() -> None:
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
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
    with open(SUBJECT_MAPS_DIR / "easy/02_simple_fork.txt") as map:
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
    with open(SUBJECT_MAPS_DIR / "easy/03_basic_capacity.txt") as map:
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
        SUBJECT_MAPS_DIR / "challenger/01_the_impossible_dream.txt"
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
    with open(OWN_MAPS_DIR / "ok/parse_ok01.txt") as map:
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
    with open(OWN_MAPS_DIR / "ok/parse_ok02.txt") as map:
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
    errors = OWN_MAPS_DIR / "error"
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
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": "0"},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_02() -> None:
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(31)},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_03() -> None:
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": secrets.token_urlsafe(16)},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_04() -> None:
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={"token": "000000000000000000000000000"},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_create_simulation_bad_token_05() -> None:
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as map:
        res = client.post(
            "/api/simulation",
            params={},
            files={"file": ("file", map.read(), "text/plain")}
        )

    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
