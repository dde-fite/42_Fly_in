from src.models.simulation import Simulation
from src.schema.simulation import ResponseSimulation


def simulation_to_schema(s: Simulation) -> ResponseSimulation:
    return ResponseSimulation(
        turns=int(s.turns),
        hubs=[hub.id for hub in s.hubs],
        origin=s.origin.id,
        destination=s.destination.id,
        connections=[con.id for con in s.connections],
        drones=[drone.id for drone in s.drones]
    )
