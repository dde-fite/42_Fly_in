import { railMetrics } from "./geometry"
import { TRACK_CASING } from "./palette"

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

// Draw a single track block between two points, CTC / dispatcher-panel style:
// a dark casing underneath for contrast plus a coloured block line on top.
// Round caps so the block joins cleanly with the horizontal station tracks.
export function drawBlockLine(
	ctx: CanvasRenderingContext2D,
	ax: number,
	ay: number,
	bx: number,
	by: number,
	color: string,
	scale: number,
	bold = false,
) {
	const dx = bx - ax
	const dy = by - ay
	if (dx * dx + dy * dy < 0.25) return

	const { railWidth } = railMetrics(scale)
	ctx.lineCap = "round"

	// Dark casing
	ctx.strokeStyle = TRACK_CASING
	ctx.lineWidth = railWidth * 2.3
	ctx.beginPath()
	ctx.moveTo(ax, ay)
	ctx.lineTo(bx, by)
	ctx.stroke()

	// Block line
	ctx.strokeStyle = color
	ctx.lineWidth = bold ? railWidth * 1.5 : railWidth
	ctx.beginPath()
	ctx.moveTo(ax, ay)
	ctx.lineTo(bx, by)
	ctx.stroke()
}

// Draw a drone as a CTC-style head-code label (a small bordered tag with the
// drone name) centered at (x, y). `size` is the drone glyph size used to scale
// the label.
export function drawDroneLabel(
	ctx: CanvasRenderingContext2D,
	x: number,
	y: number,
	name: string,
	color: string,
	size: number,
) {
	const fontSize = size * 0.95
	const padX = size * 0.35
	const padY = size * 0.22

	ctx.font = `bold ${fontSize}px 'Courier New', monospace`
	ctx.textAlign = "center"
	ctx.textBaseline = "middle"

	const textW = ctx.measureText(name).width
	const w = textW + padX * 2
	const h = fontSize + padY * 2
	const left = x - w / 2
	const top = y - h / 2
	const r = Math.min(size * 0.25, h / 2)

	// Rounded tag background
	ctx.beginPath()
	ctx.moveTo(left + r, top)
	ctx.arcTo(left + w, top, left + w, top + h, r)
	ctx.arcTo(left + w, top + h, left, top + h, r)
	ctx.arcTo(left, top + h, left, top, r)
	ctx.arcTo(left, top, left + w, top, r)
	ctx.closePath()
	ctx.fillStyle = "#0b0f14"
	ctx.fill()
	ctx.strokeStyle = color
	ctx.lineWidth = Math.max(1, size * 0.1)
	ctx.stroke()

	// Head code
	ctx.fillStyle = color
	ctx.fillText(name, x, y + fontSize * 0.04)
}
