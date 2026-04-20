import base64
from pydantic import AfterValidator
from typing import Annotated


def validate_token(token: str):
    padding = "=" * (-len(token) % 4)
    base64.urlsafe_b64decode(token + padding)
    return token


SimulationToken = Annotated[str, AfterValidator(validate_token)]
