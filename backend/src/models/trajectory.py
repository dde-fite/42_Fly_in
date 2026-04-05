from .hub import Hub
from .connection import Connection

Trajectory = list[Hub | Connection]
DijkstraTable = dict[Hub, tuple[float, Hub, Connection | None]]
