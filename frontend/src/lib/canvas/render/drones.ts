import { droneSizeFor, getHubBox } from "../geometry"
import { drawBlockLine, drawDroneLabel } from "../primitives"
import type { Scene } from "../scene"
import { connectionTrackLine } from "../track"
import { modelToCanvas, type View } from "../view"

export function drawDrones(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	getColor: (id: string) => string,
) {
	const { scale } = view
	const { hubs, drones, moves } = scene
	const droneSize = droneSizeFor(scale)

	// Drones mid-animation are drawn gliding along their track, not parked.
	const moving = moves ?? new Map()

	// Group parked drones by hub (excluding any currently animating).
	const dronesByHub = new Map<string, string[]>()
	for (const [droneId, drone] of drones) {
		if (moving.has(droneId)) continue
		if (!hubs.has(drone.location)) continue
		if (!dronesByHub.has(drone.location)) dronesByHub.set(drone.location, [])
		dronesByHub.get(drone.location)!.push(droneId)
	}

	// Hub drones — parked on the station tracks, one row per track.
	for (const [hubId, droneIds] of dronesByHub) {
		const hub = hubs.get(hubId)
		if (!hub) continue
		const [hx, hy] = modelToCanvas(view, ...hub.position)

		const { boxW, boxH, stationTrackSpacing, platformH, platformGap } =
			getHubBox(hub.name, scale, hub.capacity)
		const bx = hx - boxW / 2
		const by = hy - boxH / 2
		const trackAreaTop = by + platformH + platformGap
		const cap = Math.max(1, hub.capacity)
		const inset = droneSize * 1.1

		// Drones overflowing the track count stack into the same rows.
		const rows = new Map<number, string[]>()
		droneIds.forEach((id, i) => {
			const row = i % cap
			if (!rows.has(row)) rows.set(row, [])
			rows.get(row)!.push(id)
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

	// Animating drones — glide along the connection track, with a red "occupied"
	// fragment sliding underneath the drone.
	for (const [droneId, move] of moving) {
		const hubA = hubs.get(move.fromId)
		const hubB = hubs.get(move.toId)
		if (!hubA || !hubB) continue

		const [a, b] = connectionTrackLine(view, hubA, hubB, move.tA, move.tB)
		const dx = b.x - a.x
		const dy = b.y - a.y
		const len = Math.hypot(dx, dy) || 1
		const at = (p: number) => ({ x: a.x + dx * p, y: a.y + dy * p })

		// Red fragment: a short block centred on the drone, sized to the drone.
		const half = Math.min(0.5, (droneSize * 1.4) / len)
		const p0 = Math.max(0, move.progress - half)
		const p1 = Math.min(1, move.progress + half)
		const f0 = at(p0)
		const f1 = at(p1)
		drawBlockLine(ctx, f0.x, f0.y, f1.x, f1.y, "#ff1744", scale, true)

		const pos = at(move.progress)
		const name = drones.get(droneId)?.name ?? ""
		drawDroneLabel(ctx, pos.x, pos.y, name, getColor(droneId), droneSize)
	}
}
