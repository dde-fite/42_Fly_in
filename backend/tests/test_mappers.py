from src.mappers import drone_to_schema, itinerary_to_schema
from src.models import Turn, Vector, Hub, Connection, Drone, Itinerary


def _build() -> tuple[list[Hub], Drone, Itinerary]:
    """A → B → C → D line with one drone routed across the whole path."""
    turn = Turn(0)
    a = Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=3)
    b = Hub(name="B", position=Vector(x=1, y=0), turn=turn, capacity=3)
    c = Hub(name="C", position=Vector(x=2, y=0), turn=turn, capacity=2)
    d = Hub(name="D", position=Vector(x=3, y=0), turn=turn, capacity=3)
    Connection(hubs=frozenset({a, b}), turn=turn, capacity=2)
    Connection(hubs=frozenset({b, c}), turn=turn)
    Connection(hubs=frozenset({c, d}), turn=turn)
    drone = Drone(origin=a, destination=d, turn=turn)
    itinerary = Itinerary(drone=drone, hubs=[a, b, c, d], turn=turn)
    return [a, b, c, d], drone, itinerary


def test_drone_exposes_its_itinerary_id() -> None:
    _hubs, _drone, itinerary = _build()
    schema = drone_to_schema(itinerary.drone)
    assert schema.itinerary == itinerary.id


def test_drone_without_itinerary_has_no_itinerary_id() -> None:
    turn = Turn(0)
    a = Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=1)
    drone = Drone(origin=a, destination=a, turn=turn)
    schema = drone_to_schema(drone)
    assert schema.itinerary is None


def test_itinerary_schema_exposes_slots_with_entries_and_exits() -> None:
    _hubs, drone, itinerary = _build()
    schema = itinerary_to_schema(itinerary)

    assert schema.id == itinerary.id
    assert schema.drone == drone.id
    # Slots interleave hubs and connections in travel order.
    # Enter/exit turns mirror the underlying bookings; final hub has no exit.
    bookings = itinerary.bookings
    assert [s.zone for s in schema.slots] == [b.host.id for b in bookings]
    assert schema.slots[0].enter_turn == 0
    assert schema.slots[0].exit_turn == 1
    assert schema.slots[-1].exit_turn is None
