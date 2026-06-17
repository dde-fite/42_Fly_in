import { getHubBox, railMetrics, rectEdge } from "../geometry"
import { drawRail } from "../primitives"
import type { Scene } from "../scene"
import { modelToCanvas, type View } from "../view"

export function drawHubs(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
) {
	const { scale } = view
	const { hubs, connections, origin, destination, selectedHubId } = scene
	const { railWidth } = railMetrics(scale)
	const gap = Math.max(3, scale * 0.04)
	const labelH = Math.max(7, scale * 0.08)

	for (const [hubId, hub] of hubs) {
		const [x, y] = modelToCanvas(view, ...hub.position)
		const isSelected = hubId === selectedHubId
		const isOrigin = hubId === origin
		const isDestination = hubId === destination
		const droneCount = hub.drones.length
		const hasDrones = droneCount > 0

		const { boxW, boxH, fontSize, trackSpacing, platformH, platformGap } =
			getHubBox(hub.name, scale, hub.capacity)

		const borderColor = isSelected
			? "#ffee58"
			: isOrigin
				? "#00e676"
				: isDestination
					? "#ff1744"
					: hasDrones
						? "#ff8f00"
						: "#00acc1"
		const platBg = isOrigin ? "#112b11" : isDestination ? "#2b1111" : "#0d1f1f"

		// ── Station geometry ──────────────────────────────────────────────
		const bx = x - boxW / 2
		const by = y - boxH / 2
		const trackAreaTop = by + platformH + platformGap
		const stationTrackY = (t: number) => trackAreaTop + (t + 0.5) * trackSpacing

		// ── Throat: route each connection's tracks into the station tracks ──
		for (const [, conn] of connections) {
			const otherHubId =
				conn.hubs[0] === hubId
					? conn.hubs[1]
					: conn.hubs[1] === hubId
						? conn.hubs[0]
						: null
			if (!otherHubId) continue
			const otherHub = hubs.get(otherHubId)
			if (!otherHub) continue
			const [ox, oy] = modelToCanvas(view, ...otherHub.position)
			const ddx = ox - x,
				ddy = oy - y
			const dd = Math.sqrt(ddx * ddx + ddy * ddy)
			if (dd < 1) continue
			const ux = ddx / dd,
				uy = ddy / dd
			const px = -uy,
				py = ux
			const [ex, ey] = rectEdge(x, y, boxW, boxH, ux, uy)
			const span = (conn.capacity - 1) * trackSpacing
			// Station side the connection leans toward
			const sx = ux >= 0 ? bx + boxW : bx
			// Centred mapping of connection tracks onto station tracks
			const idxOff = Math.floor((hub.capacity - conn.capacity) / 2)
			for (let t = 0; t < conn.capacity; t++) {
				const off = -span / 2 + t * trackSpacing
				// Connection track endpoint (matches drawConnections start at edge+gap)
				const cx = ex + ux * gap + px * off
				const cy = ey + uy * gap + py * off
				const sIdx = Math.max(0, Math.min(hub.capacity - 1, idxOff + t))
				drawRail(ctx, sx, stationTrackY(sIdx), cx, cy, "#2e7d32", railWidth)
			}
		}

		// ── Station body ──────────────────────────────────────────────────

		// Overall background
		ctx.fillStyle = isOrigin ? "#091a09" : isDestination ? "#1a0909" : "#080f0f"
		ctx.fillRect(bx, by, boxW, boxH)

		// Top platform (anden)
		ctx.fillStyle = platBg
		ctx.fillRect(bx, by, boxW, platformH)
		ctx.strokeStyle = borderColor
		ctx.lineWidth = Math.max(0.5, scale * 0.008)
		ctx.strokeRect(bx, by, boxW, platformH)

		// Bottom platform (anden)
		ctx.fillStyle = platBg
		ctx.fillRect(bx, by + boxH - platformH, boxW, platformH)
		ctx.strokeRect(bx, by + boxH - platformH, boxW, platformH)

		// Single track line running horizontally through the station
		for (let t = 0; t < hub.capacity; t++) {
			const trackY = stationTrackY(t)
			ctx.strokeStyle = "#2e7d32"
			ctx.lineWidth = railWidth
			ctx.lineCap = "round"
			ctx.beginPath()
			ctx.moveTo(bx, trackY)
			ctx.lineTo(bx + boxW, trackY)
			ctx.stroke()
			// Track number badge (small)
			if (scale > 50) {
				ctx.fillStyle = "#1a3a1a"
				ctx.font = `${Math.max(5, scale * 0.065)}px 'Courier New', monospace`
				ctx.textAlign = "right"
				ctx.textBaseline = "middle"
				ctx.fillText(`${t + 1}`, bx + boxW - 3, trackY)
			}
		}

		// Outer border
		ctx.strokeStyle = borderColor
		ctx.lineWidth = isSelected
			? Math.max(2, scale * 0.03)
			: Math.max(1, scale * 0.016)
		ctx.strokeRect(bx, by, boxW, boxH)

		// Station name in top platform
		ctx.fillStyle = isOrigin ? "#00e676" : isDestination ? "#ff5252" : "#80deea"
		ctx.font = `bold ${fontSize}px 'Courier New', monospace`
		ctx.textAlign = "center"
		ctx.textBaseline = "middle"
		ctx.fillText(hub.name, x, by + platformH / 2)

		// Drone count in bottom platform
		if (hasDrones) {
			ctx.fillStyle = "#ff8f00"
			ctx.font = `${Math.max(6, scale * 0.08)}px 'Courier New', monospace`
			ctx.fillText(
				`✈ ${droneCount}/${hub.capacity}`,
				x,
				by + boxH - platformH / 2,
			)
		}

		// ORIGIN / DEST label above station
		if (isOrigin || isDestination) {
			ctx.fillStyle = isOrigin ? "#00e676" : "#ff5252"
			ctx.font = `bold ${labelH}px 'Courier New', monospace`
			ctx.textAlign = "center"
			ctx.fillText(isOrigin ? "ORIGIN" : "DEST", x, by - labelH * 0.7)
		}
	}
}
