from typing import Any
from uuid import UUID


def assert_is_uuid(value: Any):
    if isinstance(value, UUID):
        return True
    try:
        UUID(value)
        assert True
    except ValueError:
        assert False, f"Invalid UUID: {value}"
