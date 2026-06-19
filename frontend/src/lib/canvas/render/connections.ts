import type { Hub } from "../../../types/simulation"
import {
	TRACK,
	TRACK_BLOCKED,
	TRACK_OCCUPIED,
	TRACK_PRIORITY,
	TRACK_SELECTED,
} from "../palette"
import { drawBlockLine } from "../primitives"
import type { Scene } from "../scene"
import { connectionTrackLine, trackOffsets } from "../track"
import type { View } from "../view"

// Base track colour from the hubs a connection links: red when it reaches a
// blocked hub (hard stop), green when it reaches a priority hub, white otherwise.
function connectionAccessColor(hub1: Hub, hub2: Hub): string {
	if (hub1.access === "blocked" || hub2.access === "blocked")
		return TRACK_BLOCKED
	if (hub1.access === "priority" || hub2.access === "priority")
		return TRACK_PRIORITY
	return TRACK
}

export function drawConnections(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
) {
	const { scale } = view
	const { hubs, connections, drones, selectedConnectionId } = scene

	for (const [connId, connection] of connections) {
		const hub1 = hubs.get(connection.hubs[0])
		const hub2 = hubs.get(connection.hubs[1])
		if (!hub1 || !hub2) continue

		const cap = connection.capacity
		const { offA, offB } = trackOffsets(hub1.capacity, hub2.capacity, cap)

		// How many of this connection's tracks are taken by in-transit drones.
		const occupancy = Array.from(drones.values()).filter(
			d =>
				(d.location === connection.hubs[0] &&
					d.destination === connection.hubs[1]) ||
				(d.location === connection.hubs[1] &&
					d.destination === connection.hubs[0]),
		).length

		const selected = connId === selectedConnectionId
		const accessColor = connectionAccessColor(hub1, hub2)

		for (let t = 0; t < cap; t++) {
			const [a, b] = connectionTrackLine(view, hub1, hub2, offA + t, offB + t)
			const occupied = t < occupancy
			const color = selected
				? TRACK_SELECTED
				: occupied
					? TRACK_OCCUPIED
					: accessColor
			drawBlockLine(ctx, a.x, a.y, b.x, b.y, color, scale, selected || occupied)
		}
	}
}
