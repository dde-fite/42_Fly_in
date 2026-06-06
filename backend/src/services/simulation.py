from uuid import UUID
from fastapi import UploadFile
from src.models import SimulationToken, Simulation
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    ResponseConnection
)
from src.mappers import (
    simulation_to_schema, connection_to_schema,
    hub_to_schema, drone_to_schema
)
from src.utils.data_wrapper import (
    get_simulation, set_simulation
)
from src.io.parser import parse_map


async def register_simulation(
        token: SimulationToken,
        file: UploadFile
) -> ResponseSimulation:
    """
    Parses the file send from client, creates a simulation and saves to data
    cache with the token as the key.

    Raises:
        ParseError
        ValidationError
        SimulationConflict
    """
    map = await parse_map(file)
    await file.close()
    s = Simulation(map=map)
    set_simulation(token, s)
    return simulation_to_schema(s)


def fetch_simulation(token: SimulationToken) -> ResponseSimulation:
    s = get_simulation(token)
    return simulation_to_schema(s)


def fetch_hub(token: SimulationToken, id: UUID) -> ResponseHub | None:
    s = get_simulation(token)
    for hub in s.hubs:
        if hub.id == id:
            return hub_to_schema(hub)
    return None


def fetch_drone(token: SimulationToken, id: UUID) -> ResponseDrone | None:
    s = get_simulation(token)
    for drone in s.drones:
        if drone.id == id:
            return drone_to_schema(drone)
    return None


def fetch_connection(token: SimulationToken, id: UUID
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
    for _ in range(turns):
        s.tick()
    return simulation_to_schema(s)
