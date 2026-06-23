import pytest
import secrets
from src.models.simulation_token import validate_token


def test_valid_token_accepted() -> None:
    token = secrets.token_urlsafe(32)
    assert len(token) == 43
    assert validate_token(token) == token


def test_valid_token_returns_same_string() -> None:
    token = secrets.token_urlsafe(32)
    result = validate_token(token)
    assert result is token


def test_too_short_token_raises() -> None:
    with pytest.raises(Exception):
        validate_token("short")


def test_empty_token_raises() -> None:
    with pytest.raises(Exception):
        validate_token("")


def test_token_decoding_to_wrong_byte_count_raises() -> None:
    # token_urlsafe(31) produces 42 chars, decodes to 31 bytes (not 32)
    token_31 = secrets.token_urlsafe(31)
    assert len(token_31) == 42
    with pytest.raises(ValueError, match="Invalid token bytes"):
        validate_token(token_31)


def test_token_urlsafe_16_raises() -> None:
    # token_urlsafe(16) produces 22 chars, decodes to 16 bytes (not 32)
    token_16 = secrets.token_urlsafe(16)
    with pytest.raises(ValueError, match="Invalid token bytes"):
        validate_token(token_16)


def test_invalid_base64_chars_raises() -> None:
    # 43 chars but not valid url-safe base64
    bad = "!" * 43
    with pytest.raises(Exception):
        validate_token(bad)


def test_token_urlsafe_32_always_valid() -> None:
    for _ in range(20):
        token = secrets.token_urlsafe(32)
        assert len(token) == 43
        assert validate_token(token) == token
