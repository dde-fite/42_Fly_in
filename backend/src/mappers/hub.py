from src.models import Hub
from src.schema import ResponseHub


def hub_to_schema(h: Hub) -> ResponseHub:
    return ResponseHub(
        name=h.name,
        position=h.position,
        access=h.access,
        color=h.color.as_named(),
        drones=[drone.id for drone in h.drones],
        capacity=h.capacity,
        connections=[con.id for con in h.connections]
    )
