import pytest
from typing import Any
from dataclasses import dataclass
from src.models import Turn, Vector, Hub, Connection, Drone, Itinerary, TransitableZone

@dataclass
class TestMap:
    turn: Turn
    hubs: dict[str, Hub]
    connections: dict[str, Connection]
    drones: dict[str, Drone]

@pytest.fixture
def map_01() -> TestMap:
    """
    Makes a linear map: A ── con_ab ── B ── con_bc ── C, with 1 drone
    """
    turn = Turn(0)
    hubs = {
        "A": Hub(name="A", position=Vector(x=0, y=0), turn=turn),
        "B": Hub(name="B", position=Vector(x=1, y=0), turn=turn),
        "C": Hub(name="C", position=Vector(x=2, y=0), turn=turn)
    }
    connections = {
        "AB": Connection(hubs=frozenset({hubs["A"], hubs["B"]}), turn=turn),
        "BC": Connection(hubs=frozenset({hubs["B"], hubs["C"]}), turn=turn)
    }
    drones = {
        "1": Drone(origin=hubs["A"], destination=hubs["C"], turn=turn)
    }
    return TestMap(
        turn=turn,
        hubs=hubs,
        connections=connections,
        drones=drones
    )


def make_itinerary_01_01(map: TestMap) -> Itinerary:
    """
    Returns an itinerary for the map 01
    """
    hub_a = map.hubs["A"]
    con_ab = map.connections["AB"]
    hub_b = map.hubs["B"]
    con_bc = map.connections["BC"]
    hub_c = map.hubs["C"]

    return Itinerary(
        drone=map.drones["1"],
        zones=[hub_a, con_ab, hub_b, con_bc, hub_c],
        turn=map.turn
    )


def tick_all(map: TestMap) -> None:
    map.turn.value += 1
    for z in map.hubs.values():
        z.tick()
    for z in map.connections.values():
        z.tick()
    for d in map.drones.values():
        d.tick()
        if d.itinerary:
            d.itinerary.tick()

# ─── Tests ───────────────────────────────────────────────────────────────────


def test_itinerary_books_all_zones(map_01: TestMap) -> None:
    itinerary = make_itinerary_01_01(map_01)
    assert isinstance(map_01.drones["1"].itinerary, Itinerary)
    assert len(itinerary.bookings) == 5


# def test_itinerary_is_operative(turn, linear_map, drone_at_a):
#     itinerary = make_itinerary(drone_at_a, linear_map, turn)
#     drone_at_a.itinerary = itinerary
#     assert itinerary.operative()

# def test_all_zones_have_booking(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary

#         zones = [
#             linear_map["hub_a"],
#             linear_map["con_ab"],
#             linear_map["hub_b"],
#             linear_map["con_bc"],
#             linear_map["hub_c"],
#         ]
#         for zone in zones:
#             assert zone.get_booking_for_drone(drone_at_a) is not None

# def test_last_booking_has_no_exit_turn(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary

#         assert itinerary.bookings[-1].exit_turn is None

# def test_booking_turns_are_sequential(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary

#         bookings = itinerary.bookings
#         for i in range(len(bookings) - 1):
#             current_exit = bookings[i].exit_turn
#             next_entry = bookings[i + 1].enter_turn
#             assert current_exit is not None
#             assert current_exit.value == next_entry.value


# def test_drone_reaches_destination(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary
#         drones = [drone_at_a]

#         print_state(turn, linear_map, drones)
#         for _ in range(10):
#             tick_all(turn, linear_map, drones)
#             print_state(turn, linear_map, drones)
#             if drone_at_a.location == drone_at_a.destination:
#                 break

#         assert drone_at_a.location == linear_map["hub_c"]

# def test_drone_passes_through_hub_b(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary
#         drones = [drone_at_a]
#         visited = set()

#         for _ in range(10):
#             tick_all(turn, linear_map, drones)
#             visited.add(drone_at_a.location)
#             if drone_at_a.location == drone_at_a.destination:
#                 break

#         assert linear_map["hub_b"] in visited

# def test_drone_location_updates_each_tick(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary

#         locations = [drone_at_a.location]
#         for _ in range(5):
#             tick_all(turn, linear_map, [drone_at_a])
#             locations.append(drone_at_a.location)

#         # Al menos debe haberse movido una vez
#         assert len(set(id(loc) for loc in locations)) > 1

# def test_hub_capacity_respected(turn, linear_map):
#         """Dos drones no pueden estar en el mismo hub de capacidad 1 al mismo turno."""
#         hub_a = linear_map["hub_a"]
#         hub_c = linear_map["hub_c"]

#         drone1 = Drone(destination=hub_c, turn=turn)
#         drone1._location = hub_a
#         hub_a.drones.add(drone1)

#         drone2 = Drone(destination=hub_c, turn=turn)
#         drone2._location = hub_a
#         hub_a.drones.add(drone2)

#         itinerary1 = make_itinerary(drone1, linear_map, turn)
#         drone1.itinerary = itinerary1

#         itinerary2 = make_itinerary(drone2, linear_map, turn)
#         drone2.itinerary = itinerary2

#         # Los bookings de ambos no deben solaparse en el mismo turno en ninguna zona
#         for zone in [linear_map["hub_b"], linear_map["hub_c"]]:
#             b1 = zone.get_booking_for_drone(drone1)
#             b2 = zone.get_booking_for_drone(drone2)
#             if b1 and b2:
#                 # Sus ventanas de entrada no deben coincidir
#                 assert b1.enter_turn.value != b2.enter_turn.value


# def test_book_returns_false_if_already_booked(turn, linear_map, drone_at_a):
#         itinerary = make_itinerary(drone_at_a, linear_map, turn)
#         drone_at_a.itinerary = itinerary

#         hub_a = linear_map["hub_a"]
#         booking = hub_a.get_booking_for_drone(drone_at_a)
#         assert booking is not None

#         result = hub_a.book(booking)
#         assert result is False

# def test_book_rejected_when_at_capacity(turn, linear_map):
#         from src.core.models.slot_booking import SlotBooking

#         hub_b = linear_map["hub_b"]
#         hub_c = linear_map["hub_c"]

#         drone1 = Drone(destination=hub_c, turn=turn)
#         drone1._location = hub_b

#         drone2 = Drone(destination=hub_c, turn=turn)
#         drone2._location = hub_b

#         from src.core.models.slot_booking import SlotBooking
#         b1 = SlotBooking(host=hub_b, guest=drone1, enter_turn=Turn(1), exit_turn=Turn(3))
#         b2 = SlotBooking(host=hub_b, guest=drone2, enter_turn=Turn(1), exit_turn=Turn(3))

#         assert hub_b.book(b1) is True
#         assert hub_b.book(b2) is False


# def test_get_next_available_exit_returns_turn(turn, linear_map, drone_at_a):
#         con_ab = linear_map["con_ab"]
#         hub_b = linear_map["hub_b"]

#         result = con_ab.get_next_available_exit(turn, hub_b)
#         assert result is not None
#         assert result.value >= turn.value

# def test_get_next_available_exit_invalid_destination(turn, linear_map):
#         from src.core.errors import TrafficError
#         con_ab = linear_map["con_ab"]
#         hub_c = linear_map["hub_c"]  # no conectado a con_ab

#         with pytest.raises(TrafficError):
#             con_ab.get_next_available_exit(turn, hub_c)
