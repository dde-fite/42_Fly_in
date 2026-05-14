from dataclasses import dataclass


@dataclass(unsafe_hash=True)
class Turn:
    value: int = 0
