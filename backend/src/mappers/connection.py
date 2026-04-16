from src.schema import ResponseConnection
from src.models import Connection


def connection_to_schema(c: Connection) -> ResponseConnection:
    return ResponseConnection(
        hubs=[hub.id for hub in c.hubs],
        capacity=c.capacity
    )
