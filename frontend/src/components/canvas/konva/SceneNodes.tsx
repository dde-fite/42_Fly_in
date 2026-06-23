import type { Context } from "konva/lib/Context"
import { Shape } from "react-konva"
import {
	drawBackground,
	drawConnection,
	drawHub,
	drawHubDrones,
	drawMovingDrone,
	parkedDronesByHub,
} from "../../../canvas/render/entity"
import type { DroneMove, Scene } from "../../../canvas/scene"
import type { View } from "../../../canvas/view"
import type { Connection, Hub } from "../../../types/simulation"

// Konva's Context wraps the same Canvas2D calls the drawers use; the cast keeps
// the drawers typed against the standard context. Drawers must never touch
// `ctx.canvas` (Konva's is not an HTMLCanvasElement).
const as2d = (ctx: Context) => ctx as unknown as CanvasRenderingContext2D

// Every node is non-interactive: selection is resolved by hit-testing the click
// point in SimulationCanvas, against the same geometry these draw. sceneFunc is
// intentionally a fresh closure each render so Konva redraws on every render —
// the parent only re-renders on view/selection/data change or an animation
// frame, and time-based fills (rainbow, drone glide) must redraw every frame.

// Background grid + watermark.
export function Background({ view }: { view: View }) {
	return (
		<Shape
			listening={false}
			sceneFunc={ctx => drawBackground(as2d(ctx), view)}
		/>
	)
}

// One connection's tracks.
export function ConnectionShape({
	view,
	scene,
	connId,
	connection,
}: {
	view: View
	scene: Scene
	connId: string
	connection: Connection
}) {
	return (
		<Shape
			listening={false}
			sceneFunc={ctx =>
				drawConnection(as2d(ctx), view, scene, connId, connection)
			}
		/>
	)
}

// One station.
export function HubShape({
	view,
	scene,
	hubId,
	hub,
	moving,
}: {
	view: View
	scene: Scene
	hubId: string
	hub: Hub
	moving: Map<string, DroneMove>
}) {
	return (
		<Shape
			listening={false}
			sceneFunc={ctx => drawHub(as2d(ctx), view, scene, hubId, hub, moving)}
		/>
	)
}

// All drones (parked + gliding), drawn on top of the stations.
export function DroneNodes({
	view,
	scene,
	moving,
	getColor,
}: {
	view: View
	scene: Scene
	moving: Map<string, DroneMove>
	getColor: (id: string) => string
}) {
	return (
		<Shape
			listening={false}
			sceneFunc={ctx => {
				const c = as2d(ctx)
				for (const [hubId, ids] of parkedDronesByHub(scene, moving))
					drawHubDrones(c, view, scene, hubId, ids, getColor)
				for (const [droneId, move] of moving)
					drawMovingDrone(c, view, scene, droneId, move, getColor)
			}}
		/>
	)
}
