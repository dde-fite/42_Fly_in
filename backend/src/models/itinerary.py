from src.core.errors import ZoneNotAvailable, ExpiredItinerary
from .drone import Drone
from .transitable_zone import TransitableZone
from .turn import Turn
from .slot_booking import SlotBooking


class Itinerary:
    def __init__(
            self,
            drone: Drone,
            zones: list[TransitableZone],
            turn: Turn
    ) -> None:
        self.__drone = drone
        self.__bookings: list[SlotBooking] = []
        self.__turn = turn
        self.__operative: bool = False

        current: Turn = turn
        for i, zone in enumerate(zones):
            next_zone = zones[i + 1] if i + 1 < len(zones) else None
            entry = zone.get_next_available_entry(current)
            exit_turn: Turn | None
            if next_zone is not None:
                exit_turn = zone.get_next_available_exit(entry, next_zone)
            else:
                exit_turn = None
            booking = SlotBooking(
                zone,
                drone,
                entry,
                exit_turn
            )
            try:
                zone.book(booking)
            except ZoneNotAvailable as e:
                self.destroy()
                raise ZoneNotAvailable(e)
            self.__bookings.append(booking)
            if exit_turn is not None:
                current = exit_turn
        self.__operative = True

    @property
    def drone(self) -> Drone:
        return self.__drone

    @property
    def bookings(self) -> list[SlotBooking]:
        return self.__bookings.copy()

    def pop_booking(self) -> None:
        self.__bookings.pop(0)

    def operative(self) -> bool:
        return self.__operative

    def tick(self) -> None:
        if not self.__operative:
            return
        if len(self.__bookings) == 0 or not self.__bookings[0].exit_turn:
            self.destroy()
            return
        if self.__turn.value > self.__bookings[0].exit_turn.value:
            self.expired_itinerary()
        for b in self.__bookings:
            if b not in b.host.bookings:
                self.expired_itinerary()

    def expired_itinerary(self) -> None:
        self.destroy()
        raise ExpiredItinerary("The itinerary has expired")

    def destroy(self) -> None:
        for b in self.__bookings:
            b.host.unbook(b)
            self.__bookings.remove(b)
        if self.__drone.itinerary == self:
            self.__drone.itinerary = None
        self.__operative = False
