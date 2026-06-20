from src.models import Itinerary
from src.schema import ResponseItinerary, ResponseSlot


def itinerary_to_schema(it: Itinerary) -> ResponseItinerary:
    slots = [
        ResponseSlot(
            zone=b.host.id,
            enter_turn=b.enter_turn.value,
            exit_turn=b.exit_turn.value if b.exit_turn else None,
        )
        for b in it.bookings
    ]
    return ResponseItinerary(id=it.id, drone=it.drone.id, slots=slots)
