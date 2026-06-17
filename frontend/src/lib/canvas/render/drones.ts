import { drawDroneShape } from "../primitives"
import type { Scene } from "../scene"
import { modelToCanvas, type View } from "../view"

export function drawDrones(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	getColor: (id: string) => string,
) {
	const { scale } = view
	const { hubs, drones, connections } = scene
	const droneSize = Math.max(7, scale * 0.09)
	const hubRadius = Math.max(12, scale * 0.15)

	// Group drones by hub vs in-transit
	const dronesByHub = new Map<string, string[]>()
	const transitDrones: Array<{ id: string; location: string }> = []

	for (const [droneId, drone] of drones) {
		if (hubs.has(drone.location)) {
			if (!dronesByHub.has(drone.location)) dronesByHub.set(drone.location, [])
			dronesByHub.get(drone.location)!.push(droneId)
		} else {
			transitDrones.push({ id: droneId, location: drone.location })
		}
	}

	// Hub drones — non-overlapping circular arrangement
	for (const [hubId, droneIds] of dronesByHub) {
		const hub = hubs.get(hubId)
		if (!hub) continue
		const [hx, hy] = modelToCanvas(view, ...hub.position)
		const N = droneIds.length

		if (N === 1) {
			drawDroneShape(ctx, hx, hy, droneSize, getColor(droneIds[0]))
		} else {
			const minSpacing = droneSize * 2.8
			const arrangeR = Math.max(
				hubRadius + droneSize * 1.4,
				(N * minSpacing) / (2 * Math.PI),
			)
			for (let i = 0; i < N; i++) {
				const angle = (i / N) * Math.PI * 2 - Math.PI / 2
				drawDroneShape(
					ctx,
					hx + Math.cos(angle) * arrangeR,
					hy + Math.sin(angle) * arrangeR,
					droneSize,
					getColor(droneIds[i]),
				)
			}
		}
	}

	// Transit drones — midpoint of their connection
	for (const { id, location } of transitDrones) {
		for (const [, connection] of connections) {
			if (connection.hubs.includes(location as string)) {
				const hub1 = hubs.get(connection.hubs[0])
				const hub2 = hubs.get(connection.hubs[1])
				if (hub1 && hub2) {
					const [x1, y1] = modelToCanvas(view, ...hub1.position)
					const [x2, y2] = modelToCanvas(view, ...hub2.position)
					drawDroneShape(
						ctx,
						(x1 + x2) / 2,
						(y1 + y2) / 2,
						droneSize,
						getColor(id),
					)
					break
				}
			}
		}
	}
}
