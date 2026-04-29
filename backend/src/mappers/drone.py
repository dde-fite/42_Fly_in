from src.models import Drone
from src.schema import ResponseDrone


def drone_to_schema(d: Drone) -> ResponseDrone:
    return ResponseDrone(
        location=d.location.id,
        destination=d.destination.id
    )
