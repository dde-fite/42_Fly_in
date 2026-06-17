import { getHubBox, rectEdge } from "../geometry"
import { drawTrackSegment } from "../primitives"
import type { Scene } from "../scene"
import { modelToCanvas, type View } from "../view"

export function drawConnections(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
) {
	const { scale } = view
	const { hubs, connections, drones, selectedConnectionId } = scene
	const gap = Math.max(3, scale * 0.04)

	for (const [connId, connection] of connections) {
		const hub1 = hubs.get(connection.hubs[0])
		const hub2 = hubs.get(connection.hubs[1])
		if (!hub1 || !hub2) continue

		const [x1, y1] = modelToCanvas(view, ...hub1.position)
		const [x2, y2] = modelToCanvas(view, ...hub2.position)

		const dx = x2 - x1
		const dy = y2 - y1
		const dist = Math.sqrt(dx * dx + dy * dy)
		if (dist < 1) continue
		const ux = dx / dist
		const uy = dy / dist

		const b1 = getHubBox(hub1.name, scale, hub1.capacity)
		const b2 = getHubBox(hub2.name, scale, hub2.capacity)
		const [e1x, e1y] = rectEdge(x1, y1, b1.boxW, b1.boxH, ux, uy)
		const [e2x, e2y] = rectEdge(x2, y2, b2.boxW, b2.boxH, -ux, -uy)

		const occupancy = Array.from(drones.values()).filter(
			d =>
				(d.location === connection.hubs[0] &&
					d.destination === connection.hubs[1]) ||
				(d.location === connection.hubs[1] &&
					d.destination === connection.hubs[0]),
		).length

		drawTrackSegment(
			ctx,
			e1x + ux * gap,
			e1y + uy * gap,
			e2x - ux * gap,
			e2y - uy * gap,
			connection.capacity,
			occupancy,
			connId === selectedConnectionId,
			scale,
		)
	}
}
