from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from functools import lru_cache
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from src.core.errors import TrafficError, ZoneNotAvailable
from .turn import Turn
from .drone import Drone

if TYPE_CHECKING:
    from .slot_booking import SlotBooking
    from .hub import Hub


class TransitableZone(BaseModel, ABC):
    """
    Abstract base for any zone a drone can occupy: Hub or Connection.

    Responsibilities:
        - Track which drones are physically present (``drones``).
        - Maintain a list of time-slot bookings (``_bookings``).
        - Provide helpers to query occupancy and availability.
        - Enforce capacity constraints when accepting drones from \
            a neighbouring zone.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(default_factory=uuid4)
    drones: set[Drone] = Field(default_factory=set[Drone])
    capacity: int = Field(ge=1, default=1)
    capacity_defined: bool = False
    turn: Turn

    _bookings: list[SlotBooking] = PrivateAttr(default_factory=list)

    # ------------------------------------------------------------------
    # Booking access
    # ------------------------------------------------------------------

    @property
    def bookings(self) -> list[SlotBooking]:
        return self._bookings.copy()

    def get_booking_for_drone(self, drone: Drone) -> SlotBooking | None:
        for b in self._bookings:
            if b.guest == drone:
                return b
        return None

    # ------------------------------------------------------------------
    # Occupancy helpers
    # ------------------------------------------------------------------

    @lru_cache(maxsize=1000)
    def get_occupancy(self, turn: Turn, exclude: Drone | None = None) -> int:
        """
        Return the number of drones occupying (or booked to occupy) at *turn*.

        ``exclude`` lets the itinerary planner ignore bookings that
        already belong to the drone being routed, so a drone's own spawn
        booking does not block it from being assigned a slot in the same zone.
        """
        if turn.value == self.turn.value:
            return sum(1 for d in self.drones if d != exclude)

        occ: set[Drone] = set()
        for b in self._bookings:
            if exclude is not None and b.guest == exclude:
                continue
            enters = turn.value >= b.enter_turn.value
            exits, special = False, False
            if b.exit_turn is not None:
                exits = turn.value >= b.exit_turn.value
                special = (b.enter_turn.value == b.exit_turn.value ==
                           turn.value)
            if (enters and not exits) or special:
                occ.add(b.guest)
        return len(occ)

    # def get_occupancy_slots(self, turn: Turn, exclude: Drone | None = None) -> SlotBooking:
    #     """
    #     Return the number of drones occupying (or booked to occupy) at *turn*.

    #     ``exclude`` lets the itinerary planner ignore bookings that
    #     already belong to the drone being routed, so a drone's own spawn
    #     booking does not block it from being assigned a slot in the same zone.
    #     """
    #     if turn.value == self.turn.value:
    #         return sum(1 for d in self.drones if d != exclude)

    #     occ: set[Drone] = set()
    #     for b in self._bookings:
    #         if exclude is not None and b.guest == exclude:
    #             continue
    #         enters = turn.value >= b.enter_turn.value
    #         exits, special = False, False
    #         if b.exit_turn is not None:
    #             exits = turn.value >= b.exit_turn.value
    #             special = (b.enter_turn.value == b.exit_turn.value ==
    #                        turn.value)
    #         if (enters and not exits) or special:
    #             occ.add(b.guest)
    #     return len(occ)

    # ------------------------------------------------------------------
    # Booking management
    # ------------------------------------------------------------------

    def book(self, slot: SlotBooking, direction: Hub | None = None) -> None:
        """
        Attempt to reserve *slot* in this zone.

        Returns True on success, raises ZoneNotAvailable when the zone is
        blocked (movement cost is None) or capacity is exceeded.
        """
        if slot in self._bookings:
            raise ZoneNotAvailable("Drone have multiple bookings in the same zone")

        mov_cost = self.get_movement_cost(direction)
        if mov_cost is None:
            raise ZoneNotAvailable(
                f"Zone '{self}' is blocked and cannot be booked"
            )

        # Determine the range of turns this booking occupies.
        if slot.exit_turn is not None:
            end = slot.exit_turn.value
            # Ensure the booking spans at least the required movement cost.
            if end - slot.enter_turn.value < mov_cost:
                raise ZoneNotAvailable(
                    f"Booking duration ({end - slot.enter_turn.value}) is less"
                    f" than the required movement cost ({mov_cost})"
                )
        else:
            # Final destination: only check the entry turn.
            end = slot.enter_turn.value

        # Verify capacity across every turn the booking spans.
        for t in range(slot.enter_turn.value, end + 1):
            if self.get_occupancy(Turn(t), slot.guest) >= self.capacity:
                raise ZoneNotAvailable(
                    f"Zone is at capacity({self.capacity}) at turn {t}"
                )

        self._bookings.append(slot)
        self.get_occupancy.cache_clear()

    def unbook(self, slot: SlotBooking) -> None:
        if slot in self._bookings:
            self._bookings.remove(slot)
        self.get_occupancy.cache_clear()

    # ------------------------------------------------------------------
    # Physical movement
    # ------------------------------------------------------------------

    def accept_from_colateral(self, drone: Drone) -> None:
        """
        Physically move *drone* into this zone from a neighbouring one.

        Raises TrafficError if the drone has no prior booking, the zone is
        full, or the drone is already present.
        """
        if drone in self.drones:
            raise TrafficError("Drone is already in this zone")

        b = self.get_booking_for_drone(drone)
        if not b:
            raise TrafficError("Drone does not have a booking in this zone")

        if len(self.drones) + 1 > self.capacity:
            raise TrafficError("Zone capacity exceeded")

        self.drones.add(drone)
        self.get_occupancy.cache_clear()
        drone.location = self

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Purge bookings whose exit turn has already passed."""
        expired = [
            b for b in self._bookings
            if b.exit_turn and b.exit_turn.value < self.turn.value
        ]
        for b in expired:
            self.unbook(b)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def get_next_available_entry(
        self,
        from_turn: Turn,
        destination: TransitableZone | None = None
    ) -> Turn | None:
        """Return the earliest turn >= *from_turn* where a slot is free."""
        ...

    @abstractmethod
    def get_movement_cost(self, direction: Hub | None = None) -> int | None:
        """Return the number of turns required to traverse this zone, or None if blocked."""
        ...

    @abstractmethod
    def get_next_available_exit(self, from_turn: Turn, destination: Hub) -> Turn | None:
        """Return the earliest turn at which a drone can exit toward *destination*."""
        ...

    @abstractmethod
    def request_exit(self, drone: Drone) -> None:
        """Attempt to push *drone* into the next zone when its exit turn is due."""
        ...
