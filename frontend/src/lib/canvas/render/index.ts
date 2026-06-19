import type { Scene } from "../scene"
import type { View } from "../view"
import { drawConnections } from "./connections"
import { drawDrones } from "./drones"
import { drawGrid } from "./grid"
import { drawHubs } from "./hubs"

// Paint the full scene: background, grid, connections, stations, drones.
export function renderScene(
	ctx: CanvasRenderingContext2D,
	view: View,
	scene: Scene,
	getColor: (id: string) => string,
) {
	ctx.fillStyle = "#0a0a0a"
	ctx.fillRect(0, 0, view.canvasWidth, view.canvasHeight)
	drawGrid(ctx, view)

	// Background watermark, fixed top-left in screen space (CTC panel label).
	ctx.save()
	ctx.fillStyle = "rgba(255, 213, 79, 0.12)"
	ctx.font = "bold 28px 'Courier New', monospace"
	ctx.textAlign = "left"
	ctx.textBaseline = "top"
	ctx.fillText("CONTROL AREA", 20, 16)
	ctx.restore()

	drawConnections(ctx, view, scene)
	drawHubs(ctx, view, scene)
	drawDrones(ctx, view, scene, getColor)
}
