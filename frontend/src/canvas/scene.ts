import type { Connection, Drone, Hub } from "../types/simulation"

// One leg of a drone move: a glide from hub `fromId` to hub `toId` along a
// single connection track. `tA`/`tB` are the station track rows it joins at each
// end.
export interface MoveSegment {
	fromId: string
	toId: string
	tA: number
	tB: number
}

// One drone gliding from its old hub to its new hub. When the two hubs are not
// directly connected (a drone can cross several zero-cost zones in one turn) the
// move is a multi-leg path through intermediate hubs instead of a teleport.
// `progress` is eased 0→1 across the whole path.
export interface DroneMove {
	segments: MoveSegment[]
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
