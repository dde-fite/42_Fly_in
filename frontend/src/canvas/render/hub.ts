import type { Hub } from "../../types/simulation"
import { getHubBox, railMetrics } from "../geometry"
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
	TRACK_OCCUPIED,
	TRACK_SELECTED,
} from "../palette"
import type { DroneMove, Scene } from "../scene"
import { modelToCanvas, type View } from "../view"

export function drawHub(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	hubId: string,
	hub: Hub,
	moving: Map<string, DroneMove>,
) {
	const { scale } = view
	const { origin, destination, selectedHubId } = scene
	const { railWidth } = railMetrics(scale)
	const labelH = scale * 0.08

	const [x, y] = modelToCanvas(view, ...hub.position)
	const isSelected = hubId === selectedHubId
	const isOrigin = hubId === origin
	const isDestination = hubId === destination
	// The new state already parks each in-flight drone at its destination hub,
	// but it is still visually gliding on the connection. Discount arrivals so
	// the count badge and occupied-track colouring don't jump a turn ahead of
	// the drone glyph (the origin already dropped it, which is correct).
	let arriving = 0
	for (const move of moving.values()) {
		const last = move.segments[move.segments.length - 1]
		if (last && last.toId === hubId) arriving++
	}
	const droneCount = Math.max(0, hub.drones.length - arriving)
	const hasDrones = droneCount > 0

	const { boxW, boxH, fontSize, stationTrackSpacing, platformH, platformGap } =
		getHubBox(hub.name, scale, hub.capacity)

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

	const bx = x - boxW / 2
	const by = y - boxH / 2
	const trackAreaTop = by + platformH + platformGap
	const stationTrackY = (t: number) =>
		trackAreaTop + (t + 0.5) * stationTrackSpacing

	ctx.fillStyle = isOrigin ? "#091a09" : isDestination ? "#1a0909" : PANEL_BG
	ctx.fillRect(bx, by, boxW, boxH)

	if (hub.color) {
		ctx.globalAlpha = 0.45
		if (isRainbow(hub.color)) {
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

	ctx.fillStyle = platBg
	ctx.fillRect(bx, by, boxW, platformH)
	ctx.strokeStyle = borderColor
	ctx.lineWidth = scale * 0.008
	ctx.strokeRect(bx, by, boxW, platformH)

	ctx.fillStyle = platBg
	ctx.fillRect(bx, by + boxH - platformH, boxW, platformH)
	ctx.strokeRect(bx, by + boxH - platformH, boxW, platformH)

	for (let t = 0; t < hub.capacity; t++) {
		const trackY = stationTrackY(t)
		ctx.strokeStyle = t < droneCount ? TRACK_OCCUPIED : TRACK
		ctx.lineWidth = railWidth
		ctx.lineCap = "round"
		ctx.beginPath()
		ctx.moveTo(bx, trackY)
		ctx.lineTo(bx + boxW, trackY)
		ctx.stroke()
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

	if (isSelected) {
		ctx.strokeStyle = borderColor
		ctx.lineWidth = scale * 0.03
		ctx.strokeRect(bx, by, boxW, boxH)
	}

	const nameGap = scale * 0.03
	ctx.fillStyle = isOrigin ? ORIGIN : isDestination ? DEST : infoColor
	ctx.font = `bold ${fontSize}px 'Courier New', monospace`
	ctx.textAlign = "center"
	ctx.textBaseline = "bottom"
	ctx.fillText(hub.name, x, by - nameGap)
	ctx.textBaseline = "middle"

	if (hasDrones) {
		ctx.fillStyle = infoColor
		ctx.font = `${scale * 0.08}px 'Courier New', monospace`
		ctx.fillText(
			`✈ ${droneCount}/${hub.capacity}`,
			x,
			by + boxH - platformH / 2,
		)
	}

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
