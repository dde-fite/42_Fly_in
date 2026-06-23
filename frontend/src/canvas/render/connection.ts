import type { Connection, Hub } from "../../types/simulation"
import {
	TRACK,
	TRACK_BLOCKED,
	TRACK_OCCUPIED,
	TRACK_PRIORITY,
	TRACK_SELECTED,
} from "../palette"
import { drawBlockLine } from "../primitives"
import type { DroneMove, Scene } from "../scene"
import { connectionTrackLine, trackOffsets } from "../track"
import type { View } from "../view"

function connectionAccessColor(hub1: Hub, hub2: Hub): string {
	if (hub1.access === "blocked" || hub2.access === "blocked")
		return TRACK_BLOCKED
	if (hub1.access === "priority" || hub2.access === "priority")
		return TRACK_PRIORITY
	return TRACK
}

export function drawConnection(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	connId: string,
	connection: Connection,
	moving: Map<string, DroneMove>,
) {
	const { scale } = view
	const { hubs, selectedConnectionId } = scene

	const hub1 = hubs.get(connection.hubs[0])
	const hub2 = hubs.get(connection.hubs[1])
	if (!hub1 || !hub2) return

	const cap = connection.capacity
	const { offA, offB } = trackOffsets(hub1.capacity, hub2.capacity, cap)

	// Count drones currently gliding over this connection (animation only).
	// d.destination is the drone's FINAL goal hub — checking it against the
	// connection endpoints would only be correct for the last hop, so we use
	// the live animation segments instead.
	let occupancy = 0
	for (const move of moving.values()) {
		for (const seg of move.segments) {
			if (
				(seg.fromId === connection.hubs[0] &&
					seg.toId === connection.hubs[1]) ||
				(seg.fromId === connection.hubs[1] && seg.toId === connection.hubs[0])
			) {
				occupancy++
				break
			}
		}
	}

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

// The drawn track lines of a connection as [x1, y1, x2, y2] segments — shared
// by the renderer's click hit-testing.
export function connectionTrackPoints(
	view: View,
	scene: Scene,
	connection: Connection,
): [number, number, number, number][] {
	const hub1 = scene.hubs.get(connection.hubs[0])
	const hub2 = scene.hubs.get(connection.hubs[1])
	if (!hub1 || !hub2) return []
	const cap = connection.capacity
	const { offA, offB } = trackOffsets(hub1.capacity, hub2.capacity, cap)
	const lines: [number, number, number, number][] = []
	for (let t = 0; t < cap; t++) {
		const [a, b] = connectionTrackLine(view, hub1, hub2, offA + t, offB + t)
		lines.push([a.x, a.y, b.x, b.y])
	}
	return lines
}
