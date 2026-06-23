from __future__ import annotations
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4
from src.core import (ZoneNotAvailable, ExpiredItinerary, TrafficError, logger,
                      DEBUG, config)
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

    The itinerary is built from a list of Hub checkpoints. Internally it
    expands them into hub → connection → hub → connection → … → hub,
    booking a time-slot in each zone along the way.

    If any zone cannot be booked the whole itinerary is rolled back
    (destroy) and a ZoneNotAvailable exception is propagated.
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

        self.__id: UUID = uuid4()
        self.__drone = drone
        self.__bookings: list[SlotBooking] = []
        self.__turn = turn
        self.__operative: bool = False

        if logger.isEnabledFor(DEBUG) and config.EXTENDED_LOGGING:
            l_hubs = (" -> ".join(h.name for h in hubs) if hubs else "None")
            logger.debug(f"[ITINERARY {self}] Creating itinerary for drone "
                         f"{drone} through hubs {l_hubs}")

        # Build the interleaved sequence of zones:
        # [hub0, connection01, hub1, connection12, hub2, …]
        zones: list[TransitableZone] = []
        for i, hub in enumerate(hubs):
            zones.append(hub)
            if i + 1 < len(hubs):
                connection = hub.get_connection_by_hub(hubs[i + 1])
                if connection is None:
                    raise TrafficError(
                        f"No connection between '{hub.name}' and "
                        f"'{hubs[i + 1].name}'"
                    )
                zones.append(connection)

        current: Turn = Turn(turn.value)

        first = True
        entry: Turn
        for i, zone in enumerate(zones):
            next_zone = zones[i + 1] if i + 1 < len(zones) else None
            if first:
                if zone != drone.location:
                    raise TrafficError("Itineraries have to start at current "
                                       "drone location")
                entry = Turn(self.__turn.value)
                first = False
            else:
                maybe_entry = zone.get_next_available_entry(current, next_zone)
                if not maybe_entry:
                    raise TrafficError("There is no space for movement")
                entry = maybe_entry
            if next_zone is not None:
                # next_zone is always a Hub when zone is a Connection, and
                # vice-versa. get_next_available_exit needs the
                # destination hub.
                destination_hub: Hub = (
                    next_zone
                    if isinstance(next_zone, Hub)
                    else hubs[(i + 1) // 2 + 1]
                )
                exit_turn: Turn | None = zone.get_next_available_exit(
                    entry, destination_hub
                )
                if not exit_turn:
                    raise TrafficError("There is no space for movement")
            else:
                exit_turn = None
            booking = SlotBooking(
                host=zone,
                guest=drone,
                enter_turn=entry,
                exit_turn=exit_turn,
            )
            try:
                if logger.isEnabledFor(DEBUG) and config.EXTENDED_LOGGING:
                    logger.debug(f"[ITINERARY {self}] Trying to book slot for "
                                 f"drone {drone} in zone {zone}")
                zone.book(booking, direction=cast("Hub | None", next_zone))
                if logger.isEnabledFor(DEBUG) and config.EXTENDED_LOGGING:
                    logger.debug(f"[ITINERARY {self}] Booked slot for drone "
                                 f"{drone} in zone {zone}")
            except ZoneNotAvailable:
                if logger.isEnabledFor(DEBUG) and config.EXTENDED_LOGGING:
                    logger.debug(f"[ITINERARY {self}] Failed to book slot for "
                                 f"drone {drone} in zone {zone}")
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
    def id(self) -> UUID:
        """Unique identifier for this itinerary."""
        return self.__id

    @property
    def drone(self) -> Drone:
        """The drone this itinerary belongs to."""
        return self.__drone

    @property
    def bookings(self) -> list[SlotBooking]:
        """Snapshot of the current slot bookings in travel order."""
        return self.__bookings.copy()

    @property
    def operative(self) -> bool:
        """True if the itinerary is active and has not been destroyed."""
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
        """
        Validate the itinerary for the current turn.

        Destroys the itinerary if it is finished (no remaining bookings or
        no exit turn on the first booking).  Raises ExpiredItinerary if
        the drone has overstayed its exit slot or if any booking has been
        removed from its host zone.
        """
        if not self.__operative:
            return

        # Finished if no bookings remain or the first booking has no exit.
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
        """Destroy this itinerary and raise ExpiredItinerary."""
        self.destroy()
        raise ExpiredItinerary("The itinerary has expired")

    def destroy(self) -> None:
        """Unbook all reserved slots and detach from the drone."""
        # Iterate over a snapshot so we can safely remove items.
        for b in list(self.__bookings):
            try:
                b.host.unbook(b)
            except Exception as e:
                logger.warning("[ITINERARY %s] Failed to unbook slot: %s",
                               self, e)
        self.__bookings.clear()
        if logger.isEnabledFor(DEBUG):
            logger.debug(f"[ITINERARY {self}] Destroyed")

        if self.__drone.itinerary is self:
            self.__drone.itinerary = None
        self.__operative = False

    def __str__(self) -> str:
        return f"ITI-{self.drone}"
