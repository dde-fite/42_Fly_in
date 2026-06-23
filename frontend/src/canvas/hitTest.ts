import type { Hub } from "../types/simulation"
import { connectionTrackPoints } from "./render/connection"
import { hubHitBox } from "./render/hub"
import type { Scene } from "./scene"
import type { View } from "./view"

// Click selection is resolved here, against the exact same geometry the renderer
// draws, so a click on a station box or a connection track always hits.

// Id of the hub whose drawn box contains (x, y), or null.
export function hitTestHub(
	view: View,
	hubs: Map<string, Hub>,
	x: number,
	y: number,
): string | null {
	for (const [id, hub] of hubs) {
		const b = hubHitBox(view, hub)
		if (x >= b.x && x <= b.x + b.width && y >= b.y && y <= b.y + b.height)
			return id
	}
	return null
}

// Shortest distance from (px, py) to the segment (x1,y1)-(x2,y2).
function distanceToSegment(
	px: number,
	py: number,
	x1: number,
	y1: number,
	x2: number,
	y2: number,
): number {
	const dx = x2 - x1
	const dy = y2 - y1
	const lenSq = dx * dx + dy * dy
	const t = lenSq === 0 ? 0 : ((px - x1) * dx + (py - y1) * dy) / lenSq
	const cl = Math.max(0, Math.min(1, t))
	return Math.hypot(px - (x1 + cl * dx), py - (y1 + cl * dy))
}

// Id of the first connection with a track within a zoom-scaled tolerance of
// (x, y), or null.
export function hitTestConnection(
	view: View,
	scene: Scene,
	x: number,
	y: number,
): string | null {
	const tol = Math.max(6, view.scale * 0.05)
	for (const [id, connection] of scene.connections) {
		for (const [x1, y1, x2, y2] of connectionTrackPoints(
			view,
			scene,
			connection,
		)) {
			if (distanceToSegment(x, y, x1, y1, x2, y2) <= tol) return id
		}
	}
	return null
}
