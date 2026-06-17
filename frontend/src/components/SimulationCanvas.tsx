import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { createDroneColorCache } from "../lib/canvas/colors"
import { renderScene } from "../lib/canvas/render"
import type { Scene } from "../lib/canvas/scene"
import { computeAutoFit, modelToCanvas } from "../lib/canvas/view"
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

	const stateRef = useRef({
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

	const handleCanvasClick = useCallback(
		(e: React.MouseEvent<HTMLCanvasElement>) => {
			const canvas = canvasRef.current
			if (!canvas) return

			const rect = canvas.getBoundingClientRect()
			const canvasX = e.clientX - rect.left
			const canvasY = e.clientY - rect.top

			for (const [hubId, hub] of hubs) {
				const [hx, hy] = modelToCanvas(stateRef.current, ...hub.position)
				if (Math.sqrt((canvasX - hx) ** 2 + (canvasY - hy) ** 2) < 25) {
					setSelectedHubId(hubId)
					setSelectedConnectionId(null)
					return
				}
			}

			for (const [connId, connection] of connections) {
				const hub1 = hubs.get(connection.hubs[0])
				const hub2 = hubs.get(connection.hubs[1])
				if (!hub1 || !hub2) continue

				const [x1, y1] = modelToCanvas(stateRef.current, ...hub1.position)
				const [x2, y2] = modelToCanvas(stateRef.current, ...hub2.position)

				const A = canvasX - x1
				const B = canvasY - y1
				const C = x2 - x1
				const D = y2 - y1
				const lenSq = C * C + D * D
				const param = lenSq !== 0 ? (A * C + B * D) / lenSq : -1

				const xx = param < 0 ? x1 : param > 1 ? x2 : x1 + param * C
				const yy = param < 0 ? y1 : param > 1 ? y2 : y1 + param * D

				if (Math.sqrt((canvasX - xx) ** 2 + (canvasY - yy) ** 2) < 10) {
					setSelectedConnectionId(connId)
					setSelectedHubId(null)
					return
				}
			}

			setSelectedHubId(null)
			setSelectedConnectionId(null)
		},
		[hubs, connections],
	)

	const handleWheel = useCallback(
		(e: React.WheelEvent<HTMLCanvasElement>) => {
			e.preventDefault()
			const newScale = stateRef.current.scale * (e.deltaY > 0 ? 0.9 : 1.1)
			if (newScale >= 5 && newScale <= 8000) {
				stateRef.current.scale = newScale
				redraw()
			}
		},
		[redraw],
	)

	const handleMouseDown = useCallback(
		(e: React.MouseEvent<HTMLCanvasElement>) => {
			if (e.button !== 0) return
			stateRef.current.isDragging = true
			stateRef.current.dragStartX = e.clientX
			stateRef.current.dragStartY = e.clientY
		},
		[],
	)

	const handleMouseMove = useCallback(
		(e: React.MouseEvent<HTMLCanvasElement>) => {
			if (!stateRef.current.isDragging) return
			stateRef.current.panX += e.clientX - stateRef.current.dragStartX
			stateRef.current.panY += e.clientY - stateRef.current.dragStartY
			stateRef.current.dragStartX = e.clientX
			stateRef.current.dragStartY = e.clientY
			redraw()
		},
		[redraw],
	)

	const handleMouseUp = useCallback(() => {
		stateRef.current.isDragging = false
	}, [])

	const handleResize = useCallback(() => {
		const canvas = canvasRef.current
		if (!canvas?.parentElement) return
		stateRef.current.canvasWidth = canvas.parentElement.clientWidth
		stateRef.current.canvasHeight = canvas.parentElement.clientHeight
		canvas.width = stateRef.current.canvasWidth
		canvas.height = stateRef.current.canvasHeight
		redraw()
	}, [redraw])

	const handleFit = useCallback(() => {
		autoFit(hubs)
		redraw()
	}, [hubs, autoFit, redraw])

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
