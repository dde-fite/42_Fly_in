from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from src.core.errors import TrafficError
from .turn import Turn


if TYPE_CHECKING:
    from .slot_booking import SlotBooking
    from .drone import Drone
    from .hub import Hub


class TransitableZone(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID = Field(default_factory=lambda: uuid4())
    drones: set[Drone] = set()
    capacity: int = Field(ge=1, default=1)
    capacity_defined: bool = False
    turn: Turn
    _bookings: list[SlotBooking] = PrivateAttr(default=[])

    @property
    def bookings(self) -> list[SlotBooking]:
        return self._bookings.copy()

    def tick(self) -> None:
        for b in self._bookings:
            if not b.exit_turn:
                continue
            if b.exit_turn.value < self.turn.value:
                self._bookings.remove(b)

    def get_occupancy(self, turn: Turn) -> int:
        if turn.value == self.turn.value:
            return len(self.drones)
        occ: list[SlotBooking] = []
        for b in self._bookings:
            if (b.enter_turn.value <= self.turn.value and
               (not b.exit_turn or b.exit_turn.value >= self.turn.value)):
                occ.append(b)
        return len(occ)

    def get_booking_for_drone(self, drone: Drone) -> SlotBooking | None:
        for b in self._bookings:
            if b.guest == drone:
                return b
        return None

    def get_next_available_entry(self, from_turn: Turn) -> Turn:
        i = Turn(from_turn.value)
        while self.get_occupancy(i) > self.capacity:
            i.value += 1
        return i

    def book(self, slot: SlotBooking, direction: Hub | None) -> bool:
        if slot in self._bookings:
            return False
        if not slot.enter_turn and direction:
            return False
        end = slot.exit_turn.value if slot.exit_turn else max([b.enter_turn.value for b in self.bookings])
        mov_cost = self.get_movement_cost(direction)
        if mov_cost is None:
            return False
        if end - slot.enter_turn.value < mov_cost:
            return False
        for t in range(slot.enter_turn.value, end + 1):
            if self.get_occupancy(Turn(t)) >= self.capacity:
                return False
        self._bookings.append(slot)
        return True

    def unbook(self, slot: SlotBooking) -> None:
        self._bookings.remove(slot)

    def accept_from_colateral(self, drone: Drone) -> None:
        if drone in self.drones:
            raise TrafficError("Drone is already in the hub")
        if len(self.drones) + 1 > self.capacity:
            raise TrafficError("Hub capacity exceded")
        b = self.get_booking_for_drone(drone)
        if not b:
            raise TrafficError(
                "Drone not have permission to enter into hub"
            )
        self.drones.add(drone)
        drone.location = self

    @abstractmethod
    def get_movement_cost(self, direction: Hub | None = None) -> int | None: ...

    @abstractmethod
    def get_next_available_exit(self, from_turn: Turn, destination: Hub) -> Turn: ...

    @abstractmethod
    def request_exit(self, drone: Drone) -> None: ...
