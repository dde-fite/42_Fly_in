import type { Connection, Drone, Hub } from "../../types/simulation"

// Everything the renderer needs about the current simulation, independent of
// the viewport transform.
export interface Scene {
	hubs: Map<string, Hub>
	drones: Map<string, Drone>
	connections: Map<string, Connection>
	origin: string
	destination: string
	selectedHubId: string | null
	selectedConnectionId: string | null
}
