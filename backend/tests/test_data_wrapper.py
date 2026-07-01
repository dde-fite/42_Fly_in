import pytest
import secrets
from unittest.mock import MagicMock
from src.utils.data_wrapper import (get_simulation, set_simulation,
                                    simulation_exists)
from src.core.errors import SimulationNotFound


def _tok() -> str:
    return secrets.token_urlsafe(32)


def _sim() -> MagicMock:
    return MagicMock(name="Simulation")


def test_get_simulation_raises_when_not_registered() -> None:
    with pytest.raises(SimulationNotFound):
        get_simulation(_tok())


def test_set_then_get_returns_same_simulation() -> None:
    tok = _tok()
    sim = _sim()
    set_simulation(tok, sim)
    assert get_simulation(tok) is sim


def test_simulation_exists_false_for_unknown_token() -> None:
    assert simulation_exists(_tok()) is False


def test_simulation_exists_true_after_set() -> None:
    tok = _tok()
    set_simulation(tok, _sim())
    assert simulation_exists(tok) is True


def test_get_simulation_different_tokens_are_independent() -> None:
    tok_a, tok_b = _tok(), _tok()
    sim_a, sim_b = _sim(), _sim()
    set_simulation(tok_a, sim_a)
    set_simulation(tok_b, sim_b)
    assert get_simulation(tok_a) is sim_a
    assert get_simulation(tok_b) is sim_b


def test_set_overwrites_existing_simulation() -> None:
    tok = _tok()
    sim_old, sim_new = _sim(), _sim()
    set_simulation(tok, sim_old)
    set_simulation(tok, sim_new)
    assert get_simulation(tok) is sim_new
