from fastapi import UploadFile
from src.models.simulation_token import SimulationToken
from src.core import SimulationAlreadyAllocated
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    DroneRef, HubRef, ResponseConnection, ConnectionRef
)
from src.mappers import (
    simulation_to_schema, connection_to_schema,
    hub_to_schema, drone_to_schema
)
from src.utils import (
    parse_map, get_simulation, set_simulation,
    simulation_exists
)


async def register_simulation(
        token: SimulationToken,
        file: UploadFile
) -> ResponseSimulation:
    if simulation_exists(token):
        raise SimulationAlreadyAllocated(
            "Simulation token already allocated!"
        )
    s = await parse_map(file)
    await file.close()
    set_simulation(token, s)
    return simulation_to_schema(s)


def fetch_simulation(token: SimulationToken) -> ResponseSimulation:
    s = get_simulation(token)
    return simulation_to_schema(s)


def fetch_hub(token: SimulationToken, id: HubRef) -> ResponseHub | None:
    s = get_simulation(token)
    for hub in s.hubs:
        if hub.id == id:
            return hub_to_schema(hub)
    return None


def fetch_drone(token: SimulationToken, id: DroneRef) -> ResponseDrone | None:
    s = get_simulation(token)
    for drone in s.drones:
        if drone.id == id:
            return drone_to_schema(drone)
    return None


def fetch_connection(token: SimulationToken, id: ConnectionRef
                     ) -> ResponseConnection | None:
    s = get_simulation(token)
    if not s:
        return None
    for con in s.connections:
        if con.id == id:
            return connection_to_schema(con)
    return None


def execute_turn(token: SimulationToken, turns: int = 1) -> ResponseSimulation:
    s = get_simulation(token)
    s.turns += 1
    return simulation_to_schema(s)
