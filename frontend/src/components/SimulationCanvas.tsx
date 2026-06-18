import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
	type CanvasState,
	useCanvasInteraction,
} from "../hooks/useCanvasInteraction"
import { useDroneAnimation } from "../hooks/useDroneAnimation"
import { createDroneColorCache } from "../lib/canvas/colors"
import { isRainbow } from "../lib/canvas/palette"
import { renderScene } from "../lib/canvas/render"
import type { DroneMove, Scene } from "../lib/canvas/scene"
import { computeAutoFit } from "../lib/canvas/view"
import { useSimulationStore } from "../store/simulationStore"
import type { Connection, Drone, Hub, Simulation } from "../types/simulation"
import CanvasToolbar from "./canvas/CanvasToolbar"
import ConnectionDetailPanel from "./canvas/ConnectionDetailPanel"
import HubDetailPanel from "./canvas/HubDetailPanel"

interface SimulationCanvasProps {
	simulation: Simulation
}

export default function SimulationCanvas({
	simulation,
}: SimulationCanvasProps) {
	const canvasRef = useRef<HTMLCanvasElement>(null)

	const hubs = useMemo(
		() => new Map<string, Hub>(Object.entries(simulation.hubs)),
		[simulation.hubs],
	)
	const drones = useMemo(
		() => new Map<string, Drone>(Object.entries(simulation.drones)),
		[simulation.drones],
	)
	const connections = useMemo(
		() => new Map<string, Connection>(Object.entries(simulation.connections)),
		[simulation.connections],
	)

	const [selectedHubId, setSelectedHubId] = useState<string | null>(null)
	const [selectedConnectionId, setSelectedConnectionId] = useState<
		string | null
	>(null)
	const getDroneColorRef = useRef(createDroneColorCache())

	// Animated drone-move frames, written by useDroneAnimation and read by redraw.
	const movesRef = useRef<Map<string, DroneMove> | null>(null)

	// Current playback multiplier, kept in a ref so the animation reads the latest
	// value without restarting (see useDroneAnimation).
	const playbackSpeed = useSimulationStore(state => state.playbackSpeed)
	const playbackSpeedRef = useRef(playbackSpeed)
	playbackSpeedRef.current = playbackSpeed

	const stateRef = useRef<CanvasState>({
		scale: 100,
		panX: 50,
		panY: 50,
		canvasWidth: 800,
		canvasHeight: 600,
		isDragging: false,
		dragStartX: 0,
		dragStartY: 0,
		hasAutoFitted: false,
	})

	const autoFit = useCallback((hubsMap: Map<string, Hub>) => {
		const fit = computeAutoFit(
			hubsMap,
			stateRef.current.canvasWidth,
			stateRef.current.canvasHeight,
		)
		if (!fit) return
		stateRef.current.scale = fit.scale
		stateRef.current.panX = fit.panX
		stateRef.current.panY = fit.panY
	}, [])

	const redraw = useCallback(() => {
		const canvas = canvasRef.current
		if (!canvas) return
		const ctx = canvas.getContext("2d")
		if (!ctx) return

		const scene: Scene = {
			hubs,
			drones,
			connections,
			origin: simulation.origin,
			destination: simulation.destination,
			selectedHubId,
			selectedConnectionId,
			moves: movesRef.current ?? undefined,
		}
		renderScene(ctx, stateRef.current, scene, getDroneColorRef.current)
	}, [
		hubs,
		drones,
		connections,
		simulation.origin,
		simulation.destination,
		selectedHubId,
		selectedConnectionId,
	])

	useDroneAnimation({
		simulation,
		hubs,
		connections,
		playbackSpeedRef,
		movesRef,
		redraw,
	})

	const {
		handleCanvasClick,
		handleWheel,
		handleMouseDown,
		handleMouseMove,
		handleMouseUp,
		handleResize,
		handleFit,
		handleZoomIn,
		handleZoomOut,
	} = useCanvasInteraction({
		canvasRef,
		stateRef,
		hubs,
		connections,
		redraw,
		autoFit,
		onSelectHub: setSelectedHubId,
		onSelectConnection: setSelectedConnectionId,
	})

	// Keep redrawing while any hub uses the animated "rainbow" colour so its hue
	// cycles over time. Idle (no rainbow hub) leaves the canvas static.
	const hasRainbow = useMemo(
		() => Array.from(hubs.values()).some(h => isRainbow(h.color)),
		[hubs],
	)
	useEffect(() => {
		if (!hasRainbow) return
		let raf = requestAnimationFrame(function tick() {
			redraw()
			raf = requestAnimationFrame(tick)
		})
		return () => cancelAnimationFrame(raf)
	}, [hasRainbow, redraw])

	const fitViewTrigger = useSimulationStore(state => state.fitViewTrigger)

	useEffect(() => {
		if (!stateRef.current.hasAutoFitted && hubs.size > 0) {
			autoFit(hubs)
			stateRef.current.hasAutoFitted = true
		}
	}, [hubs, autoFit])

	const prevFitTriggerRef = useRef(0)
	useEffect(() => {
		if (fitViewTrigger === prevFitTriggerRef.current) return
		prevFitTriggerRef.current = fitViewTrigger
		if (fitViewTrigger === 0) return
		autoFit(hubs)
		redraw()
	}, [fitViewTrigger, hubs, autoFit, redraw])

	useEffect(() => {
		const canvas = canvasRef.current
		if (!canvas) return
		handleResize()
		window.addEventListener("resize", handleResize)
		return () => window.removeEventListener("resize", handleResize)
	}, [handleResize])

	useEffect(() => {
		redraw()
	}, [redraw])

	const selectedHub = hubs.get(selectedHubId ?? "")
	const selectedConnection = connections.get(selectedConnectionId ?? "")

	return (
		<div className='relative w-full h-full flex'>
			<canvas
				ref={canvasRef}
				className='flex-1 block bg-[#0a0a0a] cursor-grab active:cursor-grabbing'
				onClick={handleCanvasClick}
				onWheel={handleWheel}
				onMouseDown={handleMouseDown}
				onMouseMove={handleMouseMove}
				onMouseUp={handleMouseUp}
				onMouseLeave={handleMouseUp}
			/>

			<CanvasToolbar
				scale={stateRef.current.scale}
				onFit={handleFit}
				onZoomIn={handleZoomIn}
				onZoomOut={handleZoomOut}
			/>

			{selectedHub && (
				<HubDetailPanel
					hub={selectedHub}
					onClose={() => setSelectedHubId(null)}
				/>
			)}

			{selectedConnection && (
				<ConnectionDetailPanel
					connection={selectedConnection}
					hubs={hubs}
					drones={drones}
					onClose={() => setSelectedConnectionId(null)}
				/>
			)}
		</div>
	)
}
