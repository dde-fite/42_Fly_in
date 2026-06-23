import type { View } from "../view"

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
	ctx.font = "bold 48px 'Courier New', monospace"
	ctx.textAlign = "left"
	ctx.textBaseline = "top"
	ctx.fillText("CONTROL AREA", 20, 16)
	ctx.restore()
}
