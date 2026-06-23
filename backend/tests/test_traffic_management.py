import pytest
from dataclasses import dataclass
from pathlib import Path
from src.io.parser import parse_map
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
        hubs: list[Hub | None] | None = None
) -> None:
    h_copy: list[Hub] | None = None
    is_h = True
    if hubs:
        assert None not in hubs
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
    Makes a linear map: A ── con_ab ── B ── con_bc ── C, with 3 drone
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


class TestItineraryInit:
    def test_itinerary_booking_ok_01(self) -> None:
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
            [(0, 1), (1, 1), (1, 2), (2, 2), 2],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )


    def test_itinerary_booking_ok_02(self) -> None:
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
            [(0, 1), (1, 1), (1, 2), (2, 2), 2],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), 3],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 3), (3, 3), (3, 4), (4, 4), 4],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )

    def test_itinerary_booking_ok_03(self) -> None:
        turn = Turn(0)
        A = Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=3)
        B = Hub(name="B", position=Vector(x=1, y=0), turn=turn, capacity=3)
        C = Hub(name="C", position=Vector(x=2, y=0), turn=turn, capacity=2)
        D = Hub(name="D", position=Vector(x=3, y=0), turn=turn, capacity=3)
        Connection(hubs=frozenset({A, B}), turn=turn, capacity=2)
        Connection(hubs=frozenset({B, C}), turn=turn)
        Connection(hubs=frozenset({C, D}), turn=turn)
        drones = [
            Drone(origin=A, destination=D, turn=turn),
            Drone(origin=A, destination=D, turn=turn),
            Drone(origin=A, destination=D, turn=turn)
        ]
        itineraries = [
            Itinerary(drone=drones[0], hubs=[A, B, C, D], turn=turn),
            Itinerary(drone=drones[1], hubs=[A, B, C, D], turn=turn),
            Itinerary(drone=drones[2], hubs=[A, B, C, D], turn=turn)
        ]
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            [A, B, C, D]
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 1), (1, 1), (1, 3), (3, 3), (3, 4), (4, 4), 4],
            [A, B, C, D]
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 2), (2, 2), (2, 4), (4, 4), (4, 5), (5, 5), 5],
            [A, B, C, D]
        )

    def test_itinerary_booking_ok_04(self) -> None:
        turn = Turn(0)
        A = Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=10)
        B = Hub(name="B", position=Vector(x=1, y=0), turn=turn, capacity=10)
        C = Hub(name="C", position=Vector(x=2, y=0), turn=turn, capacity=10)
        Connection(hubs=frozenset({A, B}), turn=turn, capacity=10)
        Connection(hubs=frozenset({B, C}), turn=turn, capacity=1)
        drones = [
            Drone(origin=A, destination=C, turn=turn),
            Drone(origin=A, destination=C, turn=turn),
            Drone(origin=A, destination=C, turn=turn),
        ]
        itineraries = [
            Itinerary(drone=drones[0], hubs=[A, B, C], turn=turn),
            Itinerary(drone=drones[1], hubs=[A, B, C], turn=turn),
            Itinerary(drone=drones[2], hubs=[A, B, C], turn=turn),
        ]
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), 2],
            [A, B, C]
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 1), (1, 1), (1, 3), (3, 3), 3],
            [A, B, C]
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 1), (1, 1), (1, 4), (4, 4), 4],
            [A, B, C]
        )

    def test_itinerary_booking_ok_05(self) -> None:
        turn = Turn(0)
        A = Hub(name="A", position=Vector(0, 0), turn=turn, capacity=10)
        B = Hub(name="B", position=Vector(1, 0), turn=turn, capacity=10)
        C = Hub(name="C", position=Vector(2, 0), turn=turn, capacity=10)
        D = Hub(name="D", position=Vector(3, 0), turn=turn, capacity=10)
        E = Hub(name="E", position=Vector(4, 0), turn=turn, capacity=10)
        F = Hub(name="F", position=Vector(5, 0), turn=turn, capacity=10)
        Connection(hubs=frozenset({A, B}), turn=turn, capacity=5)
        Connection(hubs=frozenset({B, C}), turn=turn, capacity=4)
        Connection(hubs=frozenset({C, D}), turn=turn, capacity=3)
        Connection(hubs=frozenset({D, E}), turn=turn, capacity=2)
        Connection(hubs=frozenset({E, F}), turn=turn, capacity=1)
        drones = [
            Drone(origin=A, destination=F, turn=turn),
            Drone(origin=A, destination=F, turn=turn),
            Drone(origin=A, destination=F, turn=turn),
            Drone(origin=A, destination=F, turn=turn),
            Drone(origin=A, destination=F, turn=turn),
        ]
        itineraries = [
            Itinerary(drones[0], [A, B, C, D, E, F], turn),
            Itinerary(drones[1], [A, B, C, D, E, F], turn),
            Itinerary(drones[2], [A, B, C, D, E, F], turn),
            Itinerary(drones[3], [A, B, C, D, E, F], turn),
            Itinerary(drones[4], [A, B, C, D, E, F], turn),
        ]
        assert_bookings(
            itineraries[0].bookings,
            #   A     A<->B     B     B<->C     C     C<->D     D     D<->E
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4),
             #  E     E<->F   F
             (4, 5), (5, 5), 5],
            [A, B, C, D, E, F]
        )
        assert_bookings(
            itineraries[1].bookings,
            #   A     A<->B     B     B<->C     C     C<->D     D     D<->E
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4),
             #  E     E<->F   F
             (4, 6), (6, 6), 6],
            [A, B, C, D, E, F]
        )
        assert_bookings(
            itineraries[2].bookings,
            #   A     A<->B     B     B<->C     C     C<->D     D     D<->E
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 5), (5, 5),
             #  E     E<->F   F
             (5, 7), (7, 7), 7],
            [A, B, C, D, E, F]
        )
        assert_bookings(
            itineraries[3].bookings,
            #   A     A<->B     B     B<->C     C     C<->D     D     D<->E
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 4), (4, 4), (4, 5), (5, 5),
             #  E     E<->F   F
             (5, 8), (8, 8), 8],
            [A, B, C, D, E, F]
        )
        assert_bookings(
            itineraries[4].bookings,
            #   A     A<->B     B     B<->C     C     C<->D     D     D<->E
            [(0, 1), (1, 1), (1, 3), (3, 3), (3, 4), (4, 4), (4, 6), (6, 6),
             #  E     E<->F   F
             (6, 9), (9, 9), 9],
            [A, B, C, D, E, F]
        )

    def test_itinerary_booking_bad_01(self) -> None:
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


    def test_itinerary_booking_bad_02(self) -> None:
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


    def test_itinerary_booking_bad_03(self) -> None:
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


    def test_itinerary_booking_bad_04(self) -> None:
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

class TestControllerRequest:
    def test_controller_request_ok_01(self) -> None:
        map = make_map_01()
        sim = map_to_simulation(map)
        itinerary = sim.controller.request_itinerary(map.drones[0])
        assert itinerary
        assert_bookings(
            itinerary.bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), 2],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )

    def test_controller_request_ok_02(self) -> None:
        map = make_map_02()
        sim = map_to_simulation(map)
        itineraries: list[Itinerary] = []
        for d in map.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), 2],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), 3],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 3), (3, 3), (3, 4), (4, 4), 4],
            [
                map.hubs["A"],
                map.hubs["B"],
                map.hubs["C"]
            ]
        )

    # def test_controller_request_ok_03(self) -> None:
    #     turn = Turn(0)
    #     A = Hub(name="A", position=Vector(x=0, y=0), turn=turn, capacity=3)
    #     B = Hub(name="B", position=Vector(x=1, y=1), turn=turn, capacity=2)
    #     C = Hub(name="C", position=Vector(x=1, y=0), turn=turn, capacity=10, access=HubAccess.RESTRICTED)
    #     D = Hub(name="C", position=Vector(x=2, y=0), turn=turn, capacity=3)
    #     Connection(hubs=frozenset({A, B}), turn=turn, capacity=2)
    #     Connection(hubs=frozenset({A, C}), turn=turn, capacity=10)
    #     Connection(hubs=frozenset({B, D}), turn=turn, capacity=1)
    #     Connection(hubs=frozenset({C, D}), turn=turn, capacity=10)
    #     drones = [
    #         Drone(origin=A, destination=D, turn=turn),
    #         Drone(origin=A, destination=D, turn=turn),
    #         Drone(origin=A, destination=D, turn=turn),
    #     ]
    #     itineraries = [
    #         Itinerary(drone=drones[0], hubs=[A, B, C], turn=turn),
    #         Itinerary(drone=drones[1], hubs=[A, B, C], turn=turn),
    #         Itinerary(drone=drones[2], hubs=[A, B, C], turn=turn),
    #     ]
    #     assert_bookings(
    #         itineraries[0].bookings,
    #         [(0, 1), (1, 1), (1, 2), (2, 2), 2],
    #         [A, B, C]
    #     )
    #     assert_bookings(
    #         itineraries[1].bookings,
    #         [(0, 1), (1, 1), (1, 3), (3, 3), 3],
    #         [A, B, C]
    #     )
    #     assert_bookings(
    #         itineraries[2].bookings,
    #         [(0, 1), (1, 1), (1, 4), (4, 4), 4],
    #         [A, B, C]
    #     )

    @pytest.mark.asyncio
    async def test_controller_request_ok_easy_01(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/01_linear_path.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("waypoint1"),
            sim.get_hub_by_name("waypoint2"),
            sim.get_hub_by_name("goal")
        ]
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            route_hubs
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            route_hubs
        )

    @pytest.mark.asyncio
    async def test_controller_request_ok_easy_02(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/02_simple_fork.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            [
                sim.get_hub_by_name("start"),
                sim.get_hub_by_name("junction"),
                sim.get_hub_by_name("path_a"),
                sim.get_hub_by_name("goal")
            ]
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            [
                sim.get_hub_by_name("start"),
                sim.get_hub_by_name("junction"),
                sim.get_hub_by_name("path_b"),
                sim.get_hub_by_name("goal")
            ]
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            [
                sim.get_hub_by_name("start"),
                sim.get_hub_by_name("junction"),
                sim.get_hub_by_name("path_a"),
                sim.get_hub_by_name("goal")
            ]
        )

    @pytest.mark.asyncio
    async def test_controller_request_ok_easy_03(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "easy/03_basic_capacity.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("bottleneck"),
            sim.get_hub_by_name("wide_area"),
            sim.get_hub_by_name("goal"),
        ]
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            route_hubs
        )

        assert_bookings(
            itineraries[1].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), 3],
            route_hubs
        )

        assert_bookings(
            itineraries[2].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            route_hubs
        )

        assert_bookings(
            itineraries[3].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            route_hubs
        )

    @pytest.mark.asyncio
    async def test_controller_request_ok_medium_01(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/01_dead_end_trap.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("junction"),
            sim.get_hub_by_name("correct_path"),
            sim.get_hub_by_name("intermediate"),
            sim.get_hub_by_name("goal"),
        ]
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            route_hubs
        )
        assert_bookings(
            itineraries[1].bookings,
            [(0, 1), (1, 1), (1, 3), (3, 3), (3, 4), (4, 4), (4, 5), (5, 5), 5],
            route_hubs
        )
        assert_bookings(
            itineraries[2].bookings,
            [(0, 2), (2, 2), (2, 4), (4, 4), (4, 5), (5, 5), (5, 6), (6, 6), 6],
            route_hubs
        )
        assert_bookings(
            itineraries[3].bookings,
            [(0, 3), (3, 3), (3, 5), (5, 5), (5, 6), (6, 6), (6, 7), (7, 7), 7],
            route_hubs
        )
        assert_bookings(
            itineraries[4].bookings,
            [(0, 4), (4, 4), (4, 6), (6, 6), (6, 7), (7, 7), (7, 8), (8, 8), 8],
            route_hubs
        )

    @pytest.mark.asyncio
    async def test_controller_request_ok_medium_02(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/02_circular_loop.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("loop_a"),
            sim.get_hub_by_name("loop_b"),
            sim.get_hub_by_name("exit_point"),
            sim.get_hub_by_name("goal"),
        ]
        # loop_b→exit_point is a restricted connection (+1 extra turn).
        # start-loop_a capacity=2 lets pairs share entry turns.
        # Pairs: (d0,d1) share turn 1, (d2,d3) share turn 2, d4 turn 3, d5 turn 4.
        expected = [
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 5), (5, 5), 5],
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 4), (4, 5), (5, 6), (6, 6), 6],
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 5), (5, 6), (6, 7), (7, 7), 7],
            [(0, 2), (2, 2), (2, 4), (4, 4), (4, 6), (6, 7), (7, 8), (8, 8), 8],
            [(0, 3), (3, 3), (3, 5), (5, 5), (5, 7), (7, 8), (8, 9), (9, 9), 9],
            [(0, 4), (4, 4), (4, 6), (6, 6), (6, 8), (8, 9), (9, 10), (10, 10), 10],
        ]
        for itinerary, turns in zip(itineraries, expected):
            assert_bookings(itinerary.bookings, turns, route_hubs)

    @pytest.mark.asyncio
    async def test_controller_request_ok_medium_03(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "medium/03_priority_puzzle.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        fast_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("fast_junction"),
            sim.get_hub_by_name("fast_path"),
            sim.get_hub_by_name("merge_point"),
            sim.get_hub_by_name("goal"),
        ]
        slow_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("slow_path1"),
            sim.get_hub_by_name("slow_path2"),
            sim.get_hub_by_name("merge_point"),
            sim.get_hub_by_name("goal"),
        ]
        # d0: fast path — start(0,1) → fast_junction(1,2) → fast_path(2,3)
        #     → merge_point(3,4) → goal
        assert_bookings(
            itineraries[0].bookings,
            [(0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), 4],
            fast_hubs,
        )
        # d1: fast path — delayed 1 turn at start
        assert_bookings(
            itineraries[1].bookings,
            [(0, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), (4, 5), (5, 5), 5],
            fast_hubs,
        )
        # d2: slow path — start→slow_path1 is a restricted connection (+1 turn).
        #     merge_point-goal capacity=2 lets d2 share exit with d1.
        assert_bookings(
            itineraries[2].bookings,
            [(0, 1), (1, 2), (2, 3), (3, 3), (3, 4), (4, 4), (4, 5), (5, 5), 5],
            slow_hubs,
        )
        # d3: fast path — delayed at start; shares merge_point-goal with d2.
        assert_bookings(
            itineraries[3].bookings,
            [(0, 3), (3, 3), (3, 4), (4, 4), (4, 5), (5, 5), (5, 6), (6, 6), 6],
            fast_hubs,
        )

    @pytest.mark.asyncio
    async def test_controller_request_ok_hard_01(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/01_maze_nightmare.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        # Shortcut via maze_a2→maze_c2 (7 hubs, 13 bookings per drone).
        # The original 8-hub path maze_b1→maze_b2 was replaced by the direct
        # maze_a2→maze_c2 connection added to the map.
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("maze_a1"),
            sim.get_hub_by_name("maze_a2"),
            sim.get_hub_by_name("maze_c2"),
            sim.get_hub_by_name("bottleneck"),
            sim.get_hub_by_name("final_stretch1"),
            sim.get_hub_by_name("goal"),
        ]
        for idx, itinerary in enumerate(itineraries):
            i = idx
            # start-maze_a1 capacity=2 lets drones 0 and 1 share turn 1.
            # Drones 2+ exit start at their index turn.  maze_a1 exits
            # sequentially from turn 2 onward regardless.
            # start(0,s) conn(s,s) maze_a1(s,i+2) conn(i+2,i+2)
            # maze_a2(i+2,i+3) conn(i+3,i+3) maze_c2(i+3,i+4) conn(i+4,i+4)
            # bottleneck(i+4,i+5) conn(i+5,i+5) final_stretch1(i+5,i+6)
            # conn(i+6,i+6) goal: i+6
            s = 1 if i <= 1 else i  # start exit turn
            assert_bookings(
                itinerary.bookings,
                [
                    (0, s), (s, s),
                    (s, i+2), (i+2, i+2),
                    (i+2, i+3), (i+3, i+3),
                    (i+3, i+4), (i+4, i+4),
                    (i+4, i+5), (i+5, i+5),
                    (i+5, i+6), (i+6, i+6),
                    i+6,
                ],
                route_hubs,
            )

    @pytest.mark.asyncio
    async def test_controller_request_ok_hard_02(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/02_capacity_hell.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        # Drones spread across gate1/gate2/gate3 and priority_bypass routes —
        # each drone gets a different path. Verify all reach the destination.
        assert len(itineraries) == 12
        goal = sim.get_hub_by_name("goal")
        for itinerary in itineraries:
            assert itinerary.bookings[-1].host == goal
            assert itinerary.bookings[-1].exit_turn is None

    @pytest.mark.asyncio
    async def test_controller_request_ok_hard_03(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "hard/03_ultimate_challenge.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        # Drones spread across dist_gate1/dist_gate3 and maze paths —
        # each drone gets a different path. Verify all reach the destination.
        assert len(itineraries) == 15
        goal = sim.get_hub_by_name("goal")
        for itinerary in itineraries:
            assert itinerary.bookings[-1].host == goal
            assert itinerary.bookings[-1].exit_turn is None

    @pytest.mark.asyncio
    async def test_controller_request_ok_challenger(self) -> None:
        file = file_to_uploadfile(SUBJECT_MAPS_DIR / "challenger/01_the_impossible_dream.txt")
        map = await parse_map(file)
        sim = Simulation(map=map)
        itineraries: list[Itinerary] = []
        for d in sim.drones:
            i = sim.controller.request_itinerary(d)
            assert i
            itineraries.append(i)
        route_hubs = [
            sim.get_hub_by_name("start"),
            sim.get_hub_by_name("gate_hell1"),
            sim.get_hub_by_name("maze_trap_a1"),
            sim.get_hub_by_name("maze_trap_a2"),
            sim.get_hub_by_name("micro_gate1"),
            sim.get_hub_by_name("overflow_hell4"),
            sim.get_hub_by_name("conv_restricted7"),
            sim.get_hub_by_name("conv_restricted8"),
            sim.get_hub_by_name("conv_restricted9"),
            sim.get_hub_by_name("final_merge"),
            sim.get_hub_by_name("final_torture1"),
            sim.get_hub_by_name("final_torture2"),
            sim.get_hub_by_name("final_torture3"),
            sim.get_hub_by_name("final_torture4"),
            sim.get_hub_by_name("final_torture5"),
            sim.get_hub_by_name("impossible_goal"),
        ]
        for idx, itinerary in enumerate(itineraries):
            i = idx
            # Optimal path via overflow_hell4 shortcut (16 hubs, 19 turns/drone).
            # Restricted connections cost 1 turn (HubCost[restricted]=2 minus
            # origin hub cost=1). Four restricted hops: mg1→oh4, oh4→cr7, cr7→cr8,
            # cr8→cr9. Drone i slots in i+1 turns after turn 0 due to the
            # capacity-1 bottleneck at start→gate_hell1.
            #
            # start(0,i+1) → conn(i+1,i+1) → gh1(i+1,i+2) → conn(i+2,i+2)
            # → ma1(i+2,i+3) → conn(i+3,i+3) → ma2(i+3,i+4) → conn(i+4,i+4)
            # → mg1(i+4,i+5) → conn_r(i+5,i+6) → oh4(i+6,i+7)
            # → conn_r(i+7,i+8) → cr7(i+8,i+9) → conn_r(i+9,i+10)
            # → cr8(i+10,i+11) → conn_r(i+11,i+12) → cr9(i+12,i+13)
            # → conn(i+13,i+13) → fm(i+13,i+14) → conn(i+14,i+14)
            # → ft1(i+14,i+15) → conn(i+15,i+15) → ft2(i+15,i+16)
            # → conn(i+16,i+16) → ft3(i+16,i+17) → conn(i+17,i+17)
            # → ft4(i+17,i+18) → conn(i+18,i+18) → ft5(i+18,i+19)
            # → conn(i+19,i+19) → impossible_goal: i+19
            assert_bookings(
                itinerary.bookings,
                [
                    (0, i+1),      (i+1, i+1),
                    (i+1, i+2),    (i+2, i+2),
                    (i+2, i+3),    (i+3, i+3),
                    (i+3, i+4),    (i+4, i+4),
                    (i+4, i+5),    (i+5, i+6),    # mg1, conn restricted (+1)
                    (i+6, i+7),    (i+7, i+8),    # oh4, conn restricted (+1)
                    (i+8, i+9),    (i+9, i+10),   # cr7, conn restricted (+1)
                    (i+10, i+11),  (i+11, i+12),  # cr8, conn restricted (+1)
                    (i+12, i+13),  (i+13, i+13),  # cr9, conn normal
                    (i+13, i+14),  (i+14, i+14),
                    (i+14, i+15),  (i+15, i+15),
                    (i+15, i+16),  (i+16, i+16),
                    (i+16, i+17),  (i+17, i+17),
                    (i+17, i+18),  (i+18, i+18),
                    (i+18, i+19),  (i+19, i+19),
                    i+19,
                ],
                route_hubs,
            )


class TestTick:
    def test_ticks_ok_01(self) -> None:
        map = make_map_01()
        s = map_to_simulation(map)
        drone = next(iter(s.drones))
        s.tick()
        assert s.turn.value == 1
        assert drone.location == map.hubs["B"]
        s.tick()
        assert s.turn.value == 2
        assert drone.location == map.hubs["C"]

    def test_ticks_ok_02(self) -> None:
        map = make_map_02()
        s = map_to_simulation(map)
        drones = list(s.drones)
        s.tick()
        assert s.turn.value == 1
        assert drones[0].location == map.hubs["B"]
        assert drones[1].location == map.hubs["A"]
        assert drones[2].location == map.hubs["A"]
        s.tick()
        assert s.turn.value == 2
        assert drones[0].location == map.hubs["C"]
        assert drones[1].location == map.hubs["B"]
        assert drones[2].location == map.hubs["A"]
        s.tick()
        assert s.turn.value == 3
        assert drones[0].location == map.hubs["C"]
        assert drones[1].location == map.hubs["C"]
        assert drones[2].location == map.hubs["B"]
        s.tick()
        assert s.turn.value == 4
        assert drones[0].location == map.hubs["C"]
        assert drones[1].location == map.hubs["C"]
        assert drones[2].location == map.hubs["C"]


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
