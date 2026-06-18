import type { Connection, Hub } from "../../types/simulation"
import { getHubBox } from "./geometry"
import { connectionTrackLine, trackOffsets } from "./track"
import { modelToCanvas, type View } from "./view"

// Hit-test the drawn station rectangles. Returns the id of the hub whose box
// contains (canvasX, canvasY), or null. The box scales with name, capacity and
// zoom, so selection always matches exactly what is drawn.
export function hitTestHub(
	view: View,
	hubs: Map<string, Hub>,
	canvasX: number,
	canvasY: number,
): string | null {
	for (const [hubId, hub] of hubs) {
		const [hx, hy] = modelToCanvas(view, ...hub.position)
		const { boxW, boxH } = getHubBox(hub.name, view.scale, hub.capacity)
		if (
			Math.abs(canvasX - hx) <= boxW / 2 &&
			Math.abs(canvasY - hy) <= boxH / 2
		) {
			return hubId
		}
	}
	return null
}

// Hit-test the drawn connection track lines (edge-to-edge, per track) with a
// zoom-scaled tolerance. Returns the id of the first connection with a track
// within tolerance of (canvasX, canvasY), or null.
export function hitTestConnection(
	view: View,
	hubs: Map<string, Hub>,
	connections: Map<string, Connection>,
	canvasX: number,
	canvasY: number,
): string | null {
	const tol = Math.max(6, view.scale * 0.05)
	for (const [connId, connection] of connections) {
		const hub1 = hubs.get(connection.hubs[0])
		const hub2 = hubs.get(connection.hubs[1])
		if (!hub1 || !hub2) continue

		const cap = connection.capacity
		const { offA, offB } = trackOffsets(hub1.capacity, hub2.capacity, cap)

		for (let t = 0; t < cap; t++) {
			const [a, b] = connectionTrackLine(view, hub1, hub2, offA + t, offB + t)
			const C = b.x - a.x
			const D = b.y - a.y
			const lenSq = C * C + D * D
			const param =
				lenSq !== 0 ? ((canvasX - a.x) * C + (canvasY - a.y) * D) / lenSq : -1
			const cl = Math.max(0, Math.min(1, param))
			const xx = a.x + cl * C
			const yy = a.y + cl * D
			if (Math.hypot(canvasX - xx, canvasY - yy) <= tol) {
				return connId
			}
		}
	}
	return null
}
