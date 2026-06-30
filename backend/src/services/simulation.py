from uuid import UUID
from fastapi import UploadFile
from src.models import SimulationToken, Simulation
from src.schema import (
    ResponseSimulation, ResponseDrone, ResponseHub,
    ResponseConnection, ResponseItinerary
)
from src.mappers import (
    simulation_to_schema, connection_to_schema,
    hub_to_schema, drone_to_schema, itinerary_to_schema
)
from src.utils.data_wrapper import (
    get_simulation, set_simulation
)
from src.core.errors import SimulationAlreadyAllocated
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


def fetch_hubs(token: SimulationToken) -> dict[UUID, ResponseHub]:
    s = get_simulation(token)
    return {hub.id: hub_to_schema(hub) for hub in s.hubs}


def fetch_drones(token: SimulationToken) -> dict[UUID, ResponseDrone]:
    s = get_simulation(token)
    return {drone.id: drone_to_schema(drone) for drone in s.drones}


def fetch_connections(token: SimulationToken
                      ) -> dict[UUID, ResponseConnection]:
    s = get_simulation(token)
    return {con.id: connection_to_schema(con) for con in s.connections}


def fetch_itineraries(token: SimulationToken
                      ) -> dict[UUID, ResponseItinerary]:
    s = get_simulation(token)
    return {
        drone.itinerary.id: itinerary_to_schema(drone.itinerary)
        for drone in s.drones
        if drone.itinerary is not None
    }


def execute_turn(token: SimulationToken, turns: int = 1) -> ResponseSimulation:
    s = get_simulation(token)
    for _ in range(turns):
        s.tick()
    return simulation_to_schema(s)
