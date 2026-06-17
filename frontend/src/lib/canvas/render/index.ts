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
	drawConnections(ctx, view, scene)
	drawHubs(ctx, view, scene)
	drawDrones(ctx, view, scene, getColor)
}
