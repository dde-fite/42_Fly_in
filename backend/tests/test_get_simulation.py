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
