import base64
from pydantic import AfterValidator
from typing import Annotated


def validate_token(token: str) -> str:
    padding = "=" * (-len(token) % 4)
    decoded = base64.urlsafe_b64decode(token + padding)
    if len(decoded) != 32:
        raise ValueError("Invalid token bytes")
    return token


SimulationToken = Annotated[str, AfterValidator(validate_token)]
