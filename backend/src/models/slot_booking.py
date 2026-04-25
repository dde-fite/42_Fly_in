from dataclasses import dataclass
from .transitable_zone import TransitableZone
from .drone import Drone
from .turn import Turn


@dataclass(frozen=True)
class SlotBooking:
    host: TransitableZone
    guest: Drone
    enter_turn: Turn
    exit_turn: Turn | None
