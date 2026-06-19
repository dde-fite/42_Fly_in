import type { Connection, Drone, Hub } from "../../types/simulation"

// One drone gliding from hub `fromId` to hub `toId` along a connection track.
// `progress` is eased 0→1; `tA`/`tB` are the station track rows it joins.
export interface DroneMove {
	fromId: string
	toId: string
	tA: number
	tB: number
	progress: number
}

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
	// Drones currently animating between hubs, keyed by drone id. Absent/empty
	// when the scene is static.
	moves?: Map<string, DroneMove>
}
