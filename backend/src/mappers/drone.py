from src.models import Drone, Transit
from src.schema import ResponseDrone, ResponseTransit


def transit_to_schema(t: Transit) -> ResponseTransit:
    return ResponseTransit(
        destination=t.destination.id,
        turns_elapsed=t.turns_elapsed
    )


def drone_to_schema(d: Drone) -> ResponseDrone:
    return ResponseDrone(
        location=d.location.id,
        in_transit_to=transit_to_schema(d.in_transit_to)
    )
