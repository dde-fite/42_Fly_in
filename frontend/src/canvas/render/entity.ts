// Per-entity canvas drawers. Each station, connection and drone is its own Konva
// node (a Shape with a sceneFunc), so these draw a single entity into the Konva
// 2D context. The drawing is the same pixel logic the canvas always used; Konva
// only owns the scene graph, hit-testing, pan and zoom.

import type { Connection, Hub } from "../../types/simulation"
import { droneSizeFor, getHubBox, railMetrics } from "../geometry"
import {
	DEST,
	isRainbow,
	ORIGIN,
	PANEL_BG,
	PLATFORM_BG,
	rainbowColors,
	resolveHubColor,
	STRUCTURE,
	TRACK,
	TRACK_BLOCKED,
	TRACK_OCCUPIED,
	TRACK_PRIORITY,
	TRACK_SELECTED,
} from "../palette"
import { drawBlockLine, drawDroneLabel } from "../primitives"
import type { DroneMove, Scene } from "../scene"
import { connectionTrackLine, trackOffsets } from "../track"
import { modelToCanvas, type View } from "../view"

// ── Background ────────────────────────────────────────────────────────────────

export function drawBackground(ctx: CanvasRenderingContext2D, view: View) {
	const { canvasWidth, canvasHeight, scale, panX, panY } = view

	ctx.fillStyle = "#0a0a0a"
	ctx.fillRect(0, 0, canvasWidth, canvasHeight)

	ctx.strokeStyle = "rgba(46, 125, 50, 0.05)"
	ctx.lineWidth = 0.5
	const startX = Math.floor(-panX / scale)
	const endX = Math.ceil((canvasWidth - panX) / scale)
	for (let i = startX; i < endX; i++) {
		const x = i * scale + panX
		ctx.beginPath()
		ctx.moveTo(x, 0)
		ctx.lineTo(x, canvasHeight)
		ctx.stroke()
	}
	const startY = Math.floor(-panY / scale)
	const endY = Math.ceil((canvasHeight - panY) / scale)
	for (let i = startY; i < endY; i++) {
		const y = i * scale + panY
		ctx.beginPath()
		ctx.moveTo(0, y)
		ctx.lineTo(canvasWidth, y)
		ctx.stroke()
	}

	// Background watermark, fixed top-left in screen space (CTC panel label).
	ctx.save()
	ctx.fillStyle = "rgba(255, 213, 79, 0.12)"
	ctx.font = "bold 28px 'Courier New', monospace"
	ctx.textAlign = "left"
	ctx.textBaseline = "top"
	ctx.fillText("CONTROL AREA", 20, 16)
	ctx.restore()
}

// ── Connection ────────────────────────────────────────────────────────────────

// Base track colour from the hubs a connection links: red when it reaches a
// blocked hub (hard stop), green when it reaches a priority hub, white otherwise.
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
) {
	const { scale } = view
	const { hubs, drones, selectedConnectionId } = scene

	const hub1 = hubs.get(connection.hubs[0])
	const hub2 = hubs.get(connection.hubs[1])
	if (!hub1 || !hub2) return

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

// The drawn track lines of a connection as [x1, y1, x2, y2] segments — shared by
// the renderer's click hit-testing.
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

// ── Hub ───────────────────────────────────────────────────────────────────────

export function drawHub(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	hubId: string,
	hub: Hub,
) {
	const { scale } = view
	const { origin, destination, selectedHubId } = scene
	const { railWidth } = railMetrics(scale)
	const labelH = scale * 0.08

	const [x, y] = modelToCanvas(view, ...hub.position)
	const isSelected = hubId === selectedHubId
	const isOrigin = hubId === origin
	const isDestination = hubId === destination
	const droneCount = hub.drones.length
	const hasDrones = droneCount > 0

	const { boxW, boxH, fontSize, stationTrackSpacing, platformH, platformGap } =
		getHubBox(hub.name, scale, hub.capacity)

	// CTC info colour: amber by default, or the station's backend colour when
	// the API specifies one ("rainbow" animates). Used for the name, track
	// numbers and counts. Selection / origin / destination still override.
	const infoColor = resolveHubColor(hub.color)
	const borderColor = isSelected
		? TRACK_SELECTED
		: isOrigin
			? ORIGIN
			: isDestination
				? DEST
				: hub.color
					? infoColor
					: STRUCTURE
	const platBg = isOrigin ? "#112b11" : isDestination ? "#2b1111" : PLATFORM_BG

	// ── Station geometry ──────────────────────────────────────────────
	const bx = x - boxW / 2
	const by = y - boxH / 2
	const trackAreaTop = by + platformH + platformGap
	const stationTrackY = (t: number) =>
		trackAreaTop + (t + 0.5) * stationTrackSpacing

	// ── Station body ──────────────────────────────────────────────────

	// Overall background
	ctx.fillStyle = isOrigin ? "#091a09" : isDestination ? "#1a0909" : PANEL_BG
	ctx.fillRect(bx, by, boxW, boxH)

	// Tint the station body with its identity colour when the API gives one,
	// so the colour (and the animated "rainbow") is clearly visible on the
	// station itself, not just on the outline.
	if (hub.color) {
		ctx.globalAlpha = 0.45
		if (isRainbow(hub.color)) {
			// Show three rainbow colours at once via a diagonal gradient.
			const [c0, c1, c2] = rainbowColors(3)
			const grad = ctx.createLinearGradient(bx, by, bx + boxW, by + boxH)
			grad.addColorStop(0, c0)
			grad.addColorStop(0.5, c1)
			grad.addColorStop(1, c2)
			ctx.fillStyle = grad
		} else {
			ctx.fillStyle = infoColor
		}
		ctx.fillRect(bx, by, boxW, boxH)
		ctx.globalAlpha = 1
	}

	// Top platform (anden)
	ctx.fillStyle = platBg
	ctx.fillRect(bx, by, boxW, platformH)
	ctx.strokeStyle = borderColor
	ctx.lineWidth = scale * 0.008
	ctx.strokeRect(bx, by, boxW, platformH)

	// Bottom platform (anden)
	ctx.fillStyle = platBg
	ctx.fillRect(bx, by + boxH - platformH, boxW, platformH)
	ctx.strokeRect(bx, by + boxH - platformH, boxW, platformH)

	// Single track line running horizontally through the station.
	// Drones park on tracks 0..droneCount-1 (row = i % capacity), so those
	// tracks are occupied and drawn red.
	for (let t = 0; t < hub.capacity; t++) {
		const trackY = stationTrackY(t)
		ctx.strokeStyle = t < droneCount ? TRACK_OCCUPIED : TRACK
		ctx.lineWidth = railWidth
		ctx.lineCap = "round"
		ctx.beginPath()
		ctx.moveTo(bx, trackY)
		ctx.lineTo(bx + boxW, trackY)
		ctx.stroke()
		// Track number badge (small) — dark chip so the amber digit stays
		// readable over the white track line.
		if (scale > 50) {
			const label = `${t + 1}`
			ctx.font = `${scale * 0.065}px 'Courier New', monospace`
			ctx.textAlign = "right"
			ctx.textBaseline = "middle"
			const tw = ctx.measureText(label).width
			const padX = scale * 0.012
			const numX = bx + boxW - scale * 0.015
			const chipH = scale * 0.09
			ctx.fillStyle = PANEL_BG
			ctx.fillRect(numX - tw - padX, trackY - chipH / 2, tw + padX * 2, chipH)
			ctx.fillStyle = infoColor
			ctx.fillText(label, numX, trackY)
		}
	}

	// Selection highlight only (no permanent frame around the hub)
	if (isSelected) {
		ctx.strokeStyle = borderColor
		ctx.lineWidth = scale * 0.03
		ctx.strokeRect(bx, by, boxW, boxH)
	}

	// Station name above the station box
	const nameGap = scale * 0.03
	ctx.fillStyle = isOrigin ? ORIGIN : isDestination ? DEST : infoColor
	ctx.font = `bold ${fontSize}px 'Courier New', monospace`
	ctx.textAlign = "center"
	ctx.textBaseline = "bottom"
	ctx.fillText(hub.name, x, by - nameGap)
	ctx.textBaseline = "middle"

	// Drone count in bottom platform
	if (hasDrones) {
		ctx.fillStyle = infoColor
		ctx.font = `${scale * 0.08}px 'Courier New', monospace`
		ctx.fillText(
			`✈ ${droneCount}/${hub.capacity}`,
			x,
			by + boxH - platformH / 2,
		)
	}

	// ORIGIN / DEST label above station
	if (isOrigin || isDestination) {
		ctx.fillStyle = isOrigin ? ORIGIN : DEST
		ctx.font = `bold ${labelH}px 'Courier New', monospace`
		ctx.textAlign = "center"
		ctx.fillText(
			isOrigin ? "ORIGIN" : "DEST",
			x,
			by - nameGap - fontSize - labelH * 0.7,
		)
	}
}

// Hub hit box (top-left + size) — matches the drawn station rectangle.
export function hubHitBox(view: View, hub: Hub) {
	const [x, y] = modelToCanvas(view, ...hub.position)
	const { boxW, boxH } = getHubBox(hub.name, view.scale, hub.capacity)
	return { x: x - boxW / 2, y: y - boxH / 2, width: boxW, height: boxH }
}

// ── Drones ──────────────────────────────────────────────────────────────────

// Parked drones for one hub, laid out on its station tracks (one row per track,
// overflow stacking into the same rows).
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

// One drone gliding along its connection track, with a red "occupied" fragment
// sliding underneath it.
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

	const hubA = hubs.get(move.fromId)
	const hubB = hubs.get(move.toId)
	if (!hubA || !hubB) return

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
