from pydantic import Base64Str, AfterValidator
from typing import Annotated


def validate_token(v: Base64Str) -> Base64Str:
    if len(v) != 43:  # 32 bytes
        raise ValueError("SimulationToken must be 32 bytes")
    return v


SimulationToken = Annotated[Base64Str, AfterValidator(validate_token)]
