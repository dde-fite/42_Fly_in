from typing import Any
from uuid import UUID


def assert_uuid(value: Any) -> None:
    if isinstance(value, UUID):
        return
    try:
        UUID(value)
    except ValueError:
        assert False, f"Invalid UUID: {value}"
