import secrets
from typing import Any
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.routes import router
from tests.utils import assert_uuid


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def _create(token: str | None = None) -> str:
    """POST a simulation with easy_01 and return the token used."""
    tok = token or secrets.token_urlsafe(32)
    with open(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt") as f:
        res = client.post(
            "/api/simulation",
            params={"token": tok},
            files={"file": ("file", f.read(), "text/plain")},
        )
    assert res.status_code == 200
    return tok


def assert_simulation_response(
    data: dict[str, Any],
    turn: int,
    hubs: int,
    connections: int,
    drones: int,
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


# ── GET /token ────────────────────────────────────────────────────────────────

def test_generate_token_is_valid_length() -> None:
    res = client.get("/api/token")
    assert res.status_code == 200
    token = res.json()
    assert isinstance(token, str)
    assert len(token) == 43


# ── GET /simulation ───────────────────────────────────────────────────────────

def test_get_simulation_ok() -> None:
    tok = _create()
    res = client.get("/api/simulation", params={"token": tok})
    assert res.status_code == 200
    assert_simulation_response(res.json(), turn=0, hubs=4, connections=3, drones=2)


def test_get_simulation_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.get("/api/simulation", params={"token": tok})
    assert res.status_code == 404
    assert "detail" in res.json()


def test_get_simulation_bad_token() -> None:
    res = client.get("/api/simulation", params={"token": "bad"})
    assert res.status_code == 422
    assert "detail" in res.json()


# ── POST /simulation/step ─────────────────────────────────────────────────────

def test_advance_simulation_one_step() -> None:
    tok = _create()
    res = client.post("/api/simulation/step", params={"token": tok, "steps": 1})
    assert res.status_code == 200
    assert res.json()["turn"] == 1


def test_advance_simulation_multiple_steps() -> None:
    tok = _create()
    res = client.post("/api/simulation/step", params={"token": tok, "steps": 5})
    assert res.status_code == 200
    assert res.json()["turn"] == 5


def test_advance_simulation_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.post("/api/simulation/step", params={"token": tok, "steps": 1})
    assert res.status_code == 404
    assert "detail" in res.json()


def test_advance_simulation_bad_token() -> None:
    res = client.post("/api/simulation/step", params={"token": "bad", "steps": 1})
    assert res.status_code == 422


def test_advance_simulation_zero_steps_rejected() -> None:
    tok = _create()
    res = client.post("/api/simulation/step", params={"token": tok, "steps": 0})
    assert res.status_code == 422


# ── GET /hubs ─────────────────────────────────────────────────────────────────

def test_get_hubs_ok() -> None:
    tok = _create()
    res = client.get("/api/hubs", params={"token": tok})
    assert res.status_code == 200
    assert len(res.json()) == 4


def test_get_hubs_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.get("/api/hubs", params={"token": tok})
    assert res.status_code == 404
    assert "detail" in res.json()


# ── GET /drones ───────────────────────────────────────────────────────────────

def test_get_drones_ok() -> None:
    tok = _create()
    res = client.get("/api/drones", params={"token": tok})
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_drones_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.get("/api/drones", params={"token": tok})
    assert res.status_code == 404
    assert "detail" in res.json()


# ── GET /connections ──────────────────────────────────────────────────────────

def test_get_connections_ok() -> None:
    tok = _create()
    res = client.get("/api/connections", params={"token": tok})
    assert res.status_code == 200
    assert len(res.json()) == 3


def test_get_connections_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.get("/api/connections", params={"token": tok})
    assert res.status_code == 404
    assert "detail" in res.json()


# ── GET /itineraries ──────────────────────────────────────────────────────────

def test_get_itineraries_ok() -> None:
    tok = _create()
    res = client.get("/api/itineraries", params={"token": tok})
    assert res.status_code == 200
    assert isinstance(res.json(), dict)


def test_get_itineraries_not_found() -> None:
    tok = secrets.token_urlsafe(32)
    res = client.get("/api/itineraries", params={"token": tok})
    assert res.status_code == 404
    assert "detail" in res.json()
