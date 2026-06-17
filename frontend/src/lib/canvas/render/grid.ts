import type { View } from "../view"

export function drawGrid(ctx: CanvasRenderingContext2D, view: View) {
	const { canvasWidth, canvasHeight, scale, panX, panY } = view

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
}
