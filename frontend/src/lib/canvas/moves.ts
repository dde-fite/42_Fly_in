import type { Connection, Hub, Simulation } from "../../types/simulation"
import type { DroneMove } from "./scene"
import { trackOffsets } from "./track"

// A drone move before easing: the same shape as DroneMove minus the animated
// `progress`, plus the drone `id` so the animation can key frames by drone.
export type DroneMoveBase = Omit<DroneMove, "progress"> & { id: string }

// Compare the previous and current simulation and return one entry per drone
// that changed hubs along a real connection. Each move is assigned its own
// track row on that connection (drones sharing a connection stack on rows
// 0, 1, 2 …) centred within both stations via `trackOffsets`.
export function computeDroneMoves(
	prev: Simulation,
	next: Simulation,
	hubs: Map<string, Hub>,
	connections: Map<string, Connection>,
): DroneMoveBase[] {
	const base: DroneMoveBase[] = []
	const perConn = new Map<string, number>()

	for (const [id, drone] of Object.entries(next.drones)) {
		const old = prev.drones[id]
		if (!old || old.location === drone.location) continue
		const hubA = hubs.get(old.location)
		const hubB = hubs.get(drone.location)
		if (!hubA || !hubB) continue

		let connId: string | null = null
		let connCapacity = 1
		for (const [cid, c] of connections) {
			const [h0, h1] = c.hubs
			if (
				(h0 === old.location && h1 === drone.location) ||
				(h1 === old.location && h0 === drone.location)
			) {
				connId = cid
				connCapacity = c.capacity
				break
			}
		}
		if (!connId) continue

		// Assign each drone moving on the same connection its own track row.
		const t = perConn.get(connId) ?? 0
		perConn.set(connId, t + 1)
		const { offA, offB } = trackOffsets(
			hubA.capacity,
			hubB.capacity,
			connCapacity,
		)
		base.push({
			id,
			fromId: old.location,
			toId: drone.location,
			tA: offA + t,
			tB: offB + t,
		})
	}

	return base
}
