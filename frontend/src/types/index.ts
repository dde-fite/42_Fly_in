export interface ResponseHub {
  name: string
  position: [number, number]
  access: string
  color?: string
  drones: string[]
  capacity: number
  connections: string[]
}

export interface ResponseDrone {
  location: string
  destination: string
}

export interface ResponseConnection {
  hubs: [string, string]
  capacity: number
}

export interface ResponseSimulation {
  turn: number
  hubs: string[]
  origin: string
  destination: string
  connections: string[]
  drones: string[]
}

export interface SimulationData {
  hubDetails: Map<string, ResponseHub>
  droneDetails: Map<string, ResponseDrone>
  connectionDetails: Map<string, ResponseConnection>
}
