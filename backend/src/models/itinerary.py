from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.errors import ZoneNotAvailable, ExpiredItinerary, TrafficError
from .drone import Drone
from .hub import Hub
from .turn import Turn
from .slot_booking import SlotBooking

if TYPE_CHECKING:
    from .transitable_zone import TransitableZone


class Itinerary:
    """
    Represents a planned route for a drone through a series of hubs and the
    connections between them.

    The itinerary is built from a list of Hub checkpoints. Internally it expands
    them into the full sequence: hub → connection → hub → connection → … → hub,
    booking a time-slot in each zone along the way.

    If any zone cannot be booked the whole itinerary is rolled back (destroy) and
    a ZoneNotAvailable exception is propagated.
    """

    def __init__(
            self,
            drone: Drone,
            hubs: list[Hub],
            turn: Turn
    ) -> None:
        if len(hubs) < 1:
            raise TrafficError("An itinerary needs at least one hub")
        if drone.itinerary:
            raise TrafficError("Drone already has an itinerary assigned")

        self.__drone = drone
        self.__bookings: list[SlotBooking] = []
        self.__turn = turn
        self.__operative: bool = False

        # Build the interleaved sequence of zones:
        # [hub0, connection01, hub1, connection12, hub2, …]
        zones: list[TransitableZone] = []
        for i, hub in enumerate(hubs):
            zones.append(hub)
            if i + 1 < len(hubs):
                connection = hub.get_connection_by_hub(hubs[i + 1])
                if connection is None:
                    raise TrafficError(
                        f"No connection between '{hub.name}' and '{hubs[i + 1].name}'"
                    )
                zones.append(connection)

        current: Turn = Turn(turn.value)

        first = True
        for i, zone in enumerate(zones):
            next_zone: TransitableZone | None = zones[i + 1] if i + 1 < len(zones) else None

            if first:
                entry = Turn(self.__turn.value)
                first = False
            else:
                entry = zone.get_next_available_entry(current, next_zone)

            if next_zone is not None:
                # next_zone is always a Hub when zone is a Connection, and vice-versa.
                # get_next_available_exit needs the *destination hub*.
                destination_hub: Hub = (
                    next_zone
                    if isinstance(next_zone, Hub)
                    else hubs[(i + 1) // 2 + 1]
                )
                exit_turn: Turn | None = zone.get_next_available_exit(entry, destination_hub)
            else:
                exit_turn = None

            booking = SlotBooking(
                host=zone,
                guest=drone,
                enter_turn=entry,
                exit_turn=exit_turn,
            )

            try:
                booked = zone.book(booking, direction=next_zone)
                if not booked:
                    self.destroy()
                    raise ZoneNotAvailable(
                        f"Could not book zone '{zone}' at turn {entry.value}"
                    )
            except ZoneNotAvailable:
                self.destroy()
                raise

            self.__bookings.append(booking)
            if exit_turn is not None:
                current = Turn(exit_turn.value)

        self.__drone.itinerary = self
        self.__operative = True

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def drone(self) -> Drone:
        return self.__drone

    @property
    def bookings(self) -> list[SlotBooking]:
        return self.__bookings.copy()

    @property
    def is_operative(self) -> bool:
        return self.__operative

    # kept for backwards compatibility
    def operative(self) -> bool:
        return self.__operative

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def pop_booking(self) -> None:
        """Remove the first booking (the drone has left that zone)."""
        if self.__bookings:
            self.__bookings.pop(0)

    # ------------------------------------------------------------------
    # Tick / lifecycle
    # ------------------------------------------------------------------

    def tick(self) -> None:
        if not self.__operative:
            return

        # Itinerary is finished if no bookings remain or the last zone has no exit.
        if not self.__bookings or not self.__bookings[0].exit_turn:
            self.destroy()
            return

        # The drone has overstayed its exit slot → itinerary is stale.
        if self.__turn.value > self.__bookings[0].exit_turn.value:
            self.expired_itinerary()

        # Verify every booking is still registered in its host zone.
        for b in list(self.__bookings):
            if b not in b.host.bookings:
                self.expired_itinerary()

    def expired_itinerary(self) -> None:
        self.destroy()
        raise ExpiredItinerary("The itinerary has expired")

    def destroy(self) -> None:
        """Unbook all reserved slots and detach from the drone."""
        # Iterate over a snapshot so we can safely remove items.
        for b in list(self.__bookings):
            try:
                b.host.unbook(b)
            except Exception:
                pass  # best-effort cleanup
        self.__bookings.clear()

        if self.__drone.itinerary is self:
            self.__drone.itinerary = None
        self.__operative = False
