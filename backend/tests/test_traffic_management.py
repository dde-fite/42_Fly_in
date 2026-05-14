import pytest
from dataclasses import dataclass
from pathlib import Path
from src.utils.parser import parse_map
from src.models import Turn, Vector, Hub, Connection, Drone, Itinerary, SlotBooking, Simulation
from src.core.errors import TrafficError
from tests.utils import file_to_uploadfile


SUBJECT_MAPS_DIR = Path(__file__).parent / "maps"


@dataclass
class TestMap:
    turn: Turn
    hubs: dict[str, Hub]
    connections: dict[str, Connection]
    drones: list[Drone]


def assert_bookings(
        bookings: list[SlotBooking],
        turns: list[tuple[int, int] | int],
        hubs: list[Hub] | None = None
) -> None:
    h_copy: list[Hub] | None = None
    is_h = True
    if hubs:
        h_copy = hubs.copy()
    assert len(bookings) == len(turns), (
        f"Expected {len(turns)} bookings, got {len(bookings)}"
    )
    for i, (booking, turn) in enumerate(zip(bookings, turns)):
        if is_h:
            assert isinstance(booking.host, Hub)
            if hubs:
                assert h_copy
                assert h_copy.pop(0)
        is_h = not is_h
        if isinstance(turn, tuple):
            assert turn[0] == booking.enter_turn.value, (
                f"Booking[{i}]: expected enter_turn={turn[0]}, got "
                f"{booking.enter_turn.value}"
            )
            assert booking.exit_turn is not None, (
                f"Booking[{i}]: expected exit_turn={turn[1]}, got None"
            )
            assert turn[1] == booking.exit_turn.value, (
                f"Booking[{i}]: expected exit_turn={turn[1]}, got "
                f"{booking.exit_turn.value}"
            )
        else:
            assert turn == booking.enter_turn.value, (
                f"Booking[{i}]: expected enter_turn={turn}, got "
                f"{booking.enter_turn.value}"
            )
            assert booking.exit_turn is None, (
                f"Booking[{i}]: expected exit_turn=None, got "
                f"{booking.exit_turn.value}"
            )


def map_to_simulation(map: TestMap) -> Simulation:
    hubs = list(map.hubs.values())
    return Simulation(
        turn=map.turn,
        hubs=set(hubs),
        origin=hubs[0],
        destination=hubs[-1],
        connections={c for c in map.connections.values()},
        drones=set(map.drones),
    )


def make_map_01() -> TestMap:
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
    drones = [
        Drone(origin=hubs["A"], destination=hubs["C"], turn=turn)
    ]
    return TestMap(
        turn=turn,
        hubs=hubs,
        connections=connections,
        drones=drones
    )


def make_map_02() -> TestMap:
    """
    Makes a linear map: A ── con_ab ── B ── con_bc ── C, with 1 drone
    """
    turn = Turn(0)
    hubs = {
        "A": Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=3),
        "B": Hub(name="B", position=Vector(x=1, y=0), turn=turn, capacity=1),
        "C": Hub(name="C", position=Vector(x=2, y=0), turn=turn, capacity=3)
    }
    connections = {
        "AB": Connection(hubs=frozenset({hubs["A"], hubs["B"]}), turn=turn),
        "BC": Connection(hubs=frozenset({hubs["B"], hubs["C"]}), turn=turn)
    }
    drones = [
        Drone(origin=hubs["A"], destination=hubs["C"], turn=turn),
        Drone(origin=hubs["A"], destination=hubs["C"], turn=turn),
        Drone(origin=hubs["A"], destination=hubs["C"], turn=turn)
    ]
    return TestMap(
        turn=turn,
        hubs=hubs,
        connections=connections,
        drones=drones
    )


def make_itinerary_01(map: TestMap) -> Itinerary:
    return Itinerary(
        drone=map.drones[0],
        hubs=[
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ],
        turn=map.turn
    )


def make_itinerary_02(map: TestMap) -> list[Itinerary]:
    return [
        Itinerary(
            drone=map.drones[0],
            hubs=[
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ],
            turn=map.turn
        ),
        Itinerary(
            drone=map.drones[1],
            hubs=[
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ],
            turn=map.turn
        ),
        Itinerary(
            drone=map.drones[2],
            hubs=[
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ],
            turn=map.turn
        ),
    ]


def tick_all(map: TestMap) -> None:
    map.turn.value += 1
    for h in map.hubs.values():
        h.tick()
    for c in map.connections.values():
        c.tick()
    for d in map.drones:
        d.tick()
        if d.itinerary:
            d.itinerary.tick()

# ─── Tests ───────────────────────────────────────────────────────────────────


def test_itinerary_booking_ok_01() -> None:
    map = make_map_01()
    itinerary = make_itinerary_01(map)
    assert itinerary == map.drones[0].itinerary
    assert isinstance(itinerary, Itinerary)
    assert len(itinerary.bookings) == 5
    assert itinerary.operative
    for i, (bk, drone) in enumerate(zip(itinerary.bookings, map.drones)):
        assert bk in bk.host.bookings
        assert bk.guest == drone
        assert isinstance(bk.enter_turn, Turn)
        if i != 5:
            assert isinstance(bk.exit_turn, Turn)
        else:
            assert bk.host == map.hubs["C"]
            assert bk.exit_turn is None
    for h in map.hubs.values():
        assert len(h.bookings) == 1
    assert_bookings(
        itinerary.bookings,
        [(0, 0), (0, 1), (1, 1), (1, 2), 2],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )


def test_itinerary_booking_ok_02() -> None:
    map = make_map_02()
    itineraries = make_itinerary_02(map)
    for i, d in zip(itineraries, map.drones):
        assert isinstance(i, Itinerary)
        assert i == d.itinerary
        assert len(i.bookings) == 5
        for b in i.bookings:
            assert b in b.host.bookings
        assert i.operative
    assert_bookings(
        itineraries[0].bookings,
        [(0, 0), (0, 1), (1, 1), (1, 2), 2],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[1].bookings,
        [(0, 1), (1, 2), (2, 2), (2, 3), 3],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[2].bookings,
        [(0, 2), (2, 3), (3, 3), (3, 4), 4],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )


def test_itinerary_booking_bad_01() -> None:
    map = make_map_01()
    with pytest.raises(TrafficError):
        Itinerary(
            drone=map.drones[0],
            hubs=[
                map.hubs["C"],
                map.hubs["B"],
                map.hubs["A"]
            ],
            turn=map.turn
        )


def test_itinerary_booking_bad_02() -> None:
    map = make_map_01()
    with pytest.raises(TrafficError):
        Itinerary(
            drone=map.drones[0],
            hubs=[
                map.hubs["B"],
                map.hubs["A"],
                map.hubs["C"]
            ],
            turn=map.turn
        )


def test_itinerary_booking_bad_03() -> None:
    map = make_map_02()
    with pytest.raises(TrafficError):
        Itinerary(
            drone=map.drones[0],
            hubs=[
                map.hubs["B"],
                map.hubs["A"],
                map.hubs["C"]
            ],
            turn=map.turn
        )


def test_itinerary_booking_bad_04() -> None:
    map = make_map_02()
    Itinerary(
        drone=map.drones[0],
        hubs=[
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ],
        turn=map.turn
    )
    with pytest.raises(TrafficError):
        Itinerary(
            drone=map.drones[0],
            hubs=[
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ],
            turn=map.turn
        )


# def test_itinerary_booking_bad_02() -> None:
#     map = make_map_02()
#     itineraries = make_itinerary_02(map)
#     for i, d in zip(itineraries, map.drones):
#         assert isinstance(i, Itinerary)
#         assert i == d.itinerary
#         assert len(i.bookings) == 5
#         for b in i.bookings:
#             assert b in b.host.bookings
#         assert i.operative
#     assert_bookings(
#         itineraries[0].bookings,
#         [(0, 0), (0, 1), (1, 1), (1, 2), 2]
#     )
#     assert_bookings(
#         itineraries[1].bookings,
#         [(0, 1), (1, 2), (2, 2), (2, 3), 3]
#     )
#     assert_bookings(
#         itineraries[2].bookings,
#         [(0, 2), (2, 3), (3, 3), (3, 4), 4]
#     )


def test_controller_request_ok_01() -> None:
    map = make_map_01()
    sim = map_to_simulation(map)
    itinerary = sim.controller.request_itinerary(map.drones[0])
    assert itinerary
    assert_bookings(
        itinerary.bookings,
        [(0, 0), (0, 1), (1, 1), (1, 2), 2],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )


def test_controller_request_ok_02() -> None:
    map = make_map_02()
    sim = map_to_simulation(map)
    itineraries: list[Itinerary] = []
    for d in map.drones:
        i = sim.controller.request_itinerary(d)
        assert i
        itineraries.append(i)
    assert_bookings(
        itineraries[0].bookings,
        [(0, 0), (0, 1), (1, 1), (1, 2), 2],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[1].bookings,
        [(0, 1), (1, 2), (2, 2), (2, 3), 3],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[2].bookings,
        [(0, 2), (2, 3), (3, 3), (3, 4), 4],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )


async def test_controller_request_ok_easy_01() -> None:
    file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt")
    sim = await parse_map(file)
    itineraries: list[Itinerary] = []
    drones = list(sim.drones)
    for d in drones:
        i = sim.controller.request_itinerary(d)
        assert i
        itineraries.append(i)
    assert_bookings(
        itineraries[0].bookings,
        [(0, 0), (0, 1), (1, 1), (1, 2), 2],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[1].bookings,
        [(0, 1), (1, 2), (2, 2), (2, 3), 3],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )
    assert_bookings(
        itineraries[2].bookings,
        [(0, 2), (2, 3), (3, 3), (3, 4), 4],
        [
            map.hubs["A"],
            map.hubs["B"],
            map.hubs["C"]
        ]
    )


# def test_controller_request_03() -> None:
#     map_exp = make_map_02()
#     map_out = make_map_02()
#     make_itinerary_02(map_exp)
#     sim = map_to_simulation(map_out)
#     for d in map_out.drones:
#         sim.controller.request_itinerary(d)
#     for de, do in zip(map_exp.drones, map_out.drones):
#         assert de.itinerary
#         assert do.itinerary
#         for ie, io in zip(de.itinerary.bookings, do.itinerary.bookings):
#             assert ie.enter_turn == io.enter_turn
#             assert ie.exit_turn == io.exit_turn
#             assert ie.host == io.host


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
