import { railMetrics } from "./geometry"

// Draw a single rail line between two points.
export function drawRail(
	ctx: CanvasRenderingContext2D,
	ax: number,
	ay: number,
	bx: number,
	by: number,
	color: string,
	width: number,
) {
	const dx = bx - ax
	const dy = by - ay
	if (dx * dx + dy * dy < 0.25) return
	ctx.strokeStyle = color
	ctx.lineWidth = width
	ctx.lineCap = "round"
	ctx.beginPath()
	ctx.moveTo(ax, ay)
	ctx.lineTo(bx, by)
	ctx.stroke()
}

// Draw N parallel railroad tracks between two points.
export function drawTrackSegment(
	ctx: CanvasRenderingContext2D,
	x1: number,
	y1: number,
	x2: number,
	y2: number,
	capacity: number,
	occupancy: number,
	selected: boolean,
	scale: number,
) {
	const dx = x2 - x1
	const dy = y2 - y1
	const len = Math.sqrt(dx * dx + dy * dy)
	if (len < 1) return

	const ux = dx / len
	const uy = dy / len
	const px = -uy // perpendicular
	const py = ux

	const { trackSpacing, railWidth } = railMetrics(scale)

	const totalSpan = (capacity - 1) * trackSpacing

	for (let t = 0; t < capacity; t++) {
		const off = -totalSpan / 2 + t * trackSpacing
		const tc1x = x1 + px * off
		const tc1y = y1 + py * off
		const tc2x = x2 + px * off
		const tc2y = y2 + py * off

		const occupied = t < occupancy
		const railColor = selected ? "#ffee58" : occupied ? "#ff6d00" : "#2e7d32"

		// Single line per track
		ctx.strokeStyle = railColor
		ctx.lineWidth = railWidth
		ctx.lineCap = "round"
		ctx.beginPath()
		ctx.moveTo(tc1x, tc1y)
		ctx.lineTo(tc2x, tc2y)
		ctx.stroke()
	}
}

// Draw a quadcopter drone glyph centered at (x, y).
export function drawDroneShape(
	ctx: CanvasRenderingContext2D,
	x: number,
	y: number,
	size: number,
	color: string,
) {
	const armLen = size * 0.72
	const bodyR = size * 0.28
	const propR = size * 0.32
	const armAngles = [-135, -45, 45, 135].map(d => (d * Math.PI) / 180)

	// Arms
	ctx.strokeStyle = color
	ctx.lineWidth = Math.max(1, size * 0.18)
	ctx.lineCap = "round"
	for (const angle of armAngles) {
		ctx.beginPath()
		ctx.moveTo(x, y)
		ctx.lineTo(x + Math.cos(angle) * armLen, y + Math.sin(angle) * armLen)
		ctx.stroke()
	}

	// Propeller rings
	for (const angle of armAngles) {
		const px = x + Math.cos(angle) * armLen
		const py = y + Math.sin(angle) * armLen
		ctx.beginPath()
		ctx.arc(px, py, propR, 0, Math.PI * 2)
		ctx.fillStyle = color
		ctx.globalAlpha = 0.45
		ctx.fill()
		ctx.globalAlpha = 1
		ctx.strokeStyle = color
		ctx.lineWidth = Math.max(0.8, size * 0.12)
		ctx.stroke()
	}

	// Central body
	ctx.beginPath()
	ctx.arc(x, y, bodyR, 0, Math.PI * 2)
	ctx.fillStyle = color
	ctx.fill()
	ctx.strokeStyle = "rgba(255,255,255,0.85)"
	ctx.lineWidth = Math.max(0.8, size * 0.1)
	ctx.stroke()
}
