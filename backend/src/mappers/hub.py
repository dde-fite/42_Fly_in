from src.models import Hub
from src.schema import ResponseHub


def hub_to_schema(h: Hub) -> ResponseHub:
    return ResponseHub(
        name=h.name,
        position=(h.position.x, h.position.y),
        access=h.access.value,
        color=h.color,
        drones=[drone.id for drone in h.drones],
        capacity=h.capacity,
        connections=[con.id for con in h.connections]
    )
