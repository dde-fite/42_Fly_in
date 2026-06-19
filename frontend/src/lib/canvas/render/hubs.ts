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
import type { Scene } from "../scene"
import { modelToCanvas, type View } from "../view"

export function drawHubs(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
) {
	const { scale } = view
	const { hubs, origin, destination, selectedHubId } = scene
	const { railWidth } = railMetrics(scale)
	const labelH = scale * 0.08

	for (const [hubId, hub] of hubs) {
		const [x, y] = modelToCanvas(view, ...hub.position)
		const isSelected = hubId === selectedHubId
		const isOrigin = hubId === origin
		const isDestination = hubId === destination
		const droneCount = hub.drones.length
		const hasDrones = droneCount > 0

		const {
			boxW,
			boxH,
			fontSize,
			stationTrackSpacing,
			platformH,
			platformGap,
		} = getHubBox(hub.name, scale, hub.capacity)

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
		const platBg = isOrigin
			? "#112b11"
			: isDestination
				? "#2b1111"
				: PLATFORM_BG

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
}
