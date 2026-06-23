import { droneSizeFor, getHubBox } from "../geometry"
import { drawBlockLine, drawDroneLabel } from "../primitives"
import type { DroneMove, Scene } from "../scene"
import { connectionTrackLine, type Point } from "../track"
import { modelToCanvas, type View } from "../view"

// Parked drones for one hub, laid out on its station tracks (one row per
// track, overflow stacking into the same rows).
export function drawHubDrones(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	hubId: string,
	droneIds: string[],
	getColor: (id: string) => string,
) {
	const { scale } = view
	const { hubs, drones } = scene
	const droneSize = droneSizeFor(scale)

	const hub = hubs.get(hubId)
	if (!hub) return
	const [hx, hy] = modelToCanvas(view, ...hub.position)

	const { boxW, boxH, stationTrackSpacing, platformH, platformGap } = getHubBox(
		hub.name,
		scale,
		hub.capacity,
	)
	const bx = hx - boxW / 2
	const by = hy - boxH / 2
	const trackAreaTop = by + platformH + platformGap
	const cap = Math.max(1, hub.capacity)
	const inset = droneSize * 1.1

	// Drones overflowing the track count stack into the same rows.
	const rows = new Map<number, string[]>()
	droneIds.forEach((id, i) => {
		const row = i % cap
		const ids = rows.get(row) ?? []
		ids.push(id)
		rows.set(row, ids)
	})

	for (const [row, ids] of rows) {
		const y = trackAreaTop + (row + 0.5) * stationTrackSpacing
		const n = ids.length
		for (let k = 0; k < n; k++) {
			const x = n === 1 ? hx : bx + inset + ((boxW - inset * 2) * k) / (n - 1)
			const name = drones.get(ids[k])?.name ?? ""
			drawDroneLabel(ctx, x, y, name, getColor(ids[k]), droneSize)
		}
	}
}

// One drone gliding along its path, with a red "occupied" fragment sliding
// underneath it. The path may be several connection legs: `progress` is mapped
// across the total length so the glide spans the whole route at a steady pace.
export function drawMovingDrone(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	droneId: string,
	move: DroneMove,
	getColor: (id: string) => string,
) {
	const { scale } = view
	const { hubs, drones } = scene
	const droneSize = droneSizeFor(scale)

	// Resolve each leg to its drawn pixel endpoints; bail if any hub is missing.
	const legs: { a: Point; b: Point; len: number }[] = []
	for (const seg of move.segments) {
		const hubA = hubs.get(seg.fromId)
		const hubB = hubs.get(seg.toId)
		if (!hubA || !hubB) return
		const [a, b] = connectionTrackLine(view, hubA, hubB, seg.tA, seg.tB)
		legs.push({ a, b, len: Math.hypot(b.x - a.x, b.y - a.y) || 1 })
	}
	if (legs.length === 0) return

	const total = legs.reduce((sum, leg) => sum + leg.len, 0)

	// Position at overall path fraction p (0→1): find the leg it lands on and
	// interpolate within it.
	const at = (p: number) => {
		let target = Math.max(0, Math.min(1, p)) * total
		for (let i = 0; i < legs.length; i++) {
			const leg = legs[i]
			if (target <= leg.len || i === legs.length - 1) {
				const local = leg.len === 0 ? 0 : target / leg.len
				return {
					x: leg.a.x + (leg.b.x - leg.a.x) * local,
					y: leg.a.y + (leg.b.y - leg.a.y) * local,
				}
			}
			target -= leg.len
		}
		const last = legs[legs.length - 1]
		return { x: last.b.x, y: last.b.y }
	}

	// Red fragment: a short block centred on the drone, sized to the drone.
	const half = Math.min(0.5, (droneSize * 1.4) / total)
	const f0 = at(move.progress - half)
	const f1 = at(move.progress + half)
	drawBlockLine(ctx, f0.x, f0.y, f1.x, f1.y, "#ff1744", scale, true)

	const pos = at(move.progress)
	const name = drones.get(droneId)?.name ?? ""
	drawDroneLabel(ctx, pos.x, pos.y, name, getColor(droneId), droneSize)
}

// Group parked drones by hub, excluding any currently animating.
export function parkedDronesByHub(
	scene: Scene,
	moving: Map<string, DroneMove>,
): Map<string, string[]> {
	const byHub = new Map<string, string[]>()
	for (const [droneId, drone] of scene.drones) {
		if (moving.has(droneId)) continue
		if (!scene.hubs.has(drone.location)) continue
		const row = byHub.get(drone.location) ?? []
		row.push(droneId)
		byHub.set(drone.location, row)
	}
	return byHub
}
