from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from .turn import Turn
from .slot_booking import SlotBooking


if TYPE_CHECKING:
    from .drone import Drone


class TransitableZone(BaseModel, ABC):
    drones: set[Drone] = set()
    capacity: int = Field(ge=1, default=1)
    capacity_defined: bool = False
    turn: Turn
    _bookings: list[SlotBooking] = []

    @property
    def bookings(self) -> list[SlotBooking]:
        return self._bookings.copy()

    def tick(self) -> None:
        for b in self._bookings:
            if not b.exit_turn:
                continue
            if b.exit_turn.value > self.turn.value:
                self._bookings.remove(b)

    def get_booking_for_drone(self, drone: Drone) -> SlotBooking | None:
        for b in self._bookings:
            if b.guest == drone:
                return b
        return None

    @abstractmethod
    def get_next_available_entry(self, from_turn: Turn) -> Turn: ...

    @abstractmethod
    def get_next_available_exit(self, from_turn: Turn, destination: TransitableZone) -> Turn: ...

    @abstractmethod
    def book(self, slot: SlotBooking) -> None: ...

    @abstractmethod
    def unbook(self, slot: SlotBooking) -> None: ...

    @abstractmethod
    def can_receive_from_colateral(self, drone: Drone) -> bool: ...

    @abstractmethod
    def accept_from_colateral(self, drone: Drone) -> None: ...

    @abstractmethod
    def request_exit(self, drone: Drone) -> None: ...
