from .hub import Hub
from .drone import Drone
from .connection import Connection
from .transitable_zone import TransitableZone
from .itinerary import Itinerary

Hub.model_rebuild()
Drone.model_rebuild()
Connection.model_rebuild()
TransitableZone.model_rebuild()
