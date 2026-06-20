import type Konva from "konva"
import { useCallback, useMemo, useReducer, useRef, useState } from "react"
import { Layer, Stage } from "react-konva"
import { createDroneColorCache } from "../canvas/colors"
import { hitTestConnection, hitTestHub } from "../canvas/hitTest"
import type { DroneMove, Scene } from "../canvas/scene"
import { useCanvasView } from "../hooks/useCanvasView"
import { useDroneAnimation } from "../hooks/useDroneAnimation"
import { useRainbowRedraw } from "../hooks/useRainbowRedraw"
import { useSimulationStore } from "../store/simulationStore"
import type { Connection, Drone, Hub, Simulation } from "../types/simulation"
import CanvasToolbar from "./canvas/CanvasToolbar"
import ConnectionDetailPanel from "./canvas/ConnectionDetailPanel"
import HubDetailPanel from "./canvas/HubDetailPanel"
import {
	Background,
	ConnectionShape,
	DroneNodes,
	HubShape,
} from "./canvas/konva/SceneNodes"

interface SimulationCanvasProps {
	simulation: Simulation
}

const EMPTY_MOVES: Map<string, DroneMove> = new Map()

export default function SimulationCanvas({
	simulation,
}: SimulationCanvasProps) {
	const containerRef = useRef<HTMLDivElement>(null)

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

	// Viewport (pan/zoom/size) and the pointer handlers that drive it.
	const {
		view,
		autoFit,
		zoomIn,
		zoomOut,
		wasDragging,
		handleWheel,
		handleMouseDown,
		handleMouseMove,
		endDrag,
	} = useCanvasView(hubs, containerRef)

	// Animated drone-move frames, written by useDroneAnimation; a render bump
	// forces a redraw each animation frame (Konva reads movesRef during render).
	const movesRef = useRef<Map<string, DroneMove> | null>(null)
	// useReducer dispatch is referentially stable, so it doubles as the redraw
	// signal (Konva reads movesRef during render).
	const [, bumpRender] = useReducer((n: number) => n + 1, 0)

	// Current playback multiplier, kept in a ref so the animation reads the latest
	// value without restarting (see useDroneAnimation).
	const playbackSpeed = useSimulationStore(state => state.playbackSpeed)
	const playbackSpeedRef = useRef(playbackSpeed)
	playbackSpeedRef.current = playbackSpeed

	useDroneAnimation({
		simulation,
		hubs,
		connections,
		playbackSpeedRef,
		movesRef,
		redraw: bumpRender,
	})

	// Cycle rainbow stations while any exist.
	useRainbowRedraw(hubs, bumpRender)

	// Memoized so the per-frame render bumps (drone glide / rainbow) don't allocate
	// new arrays/objects that would force every Konva shape to redraw.
	const hubEntries = useMemo(() => Array.from(hubs), [hubs])
	const connEntries = useMemo(() => Array.from(connections), [connections])
	const moving = movesRef.current ?? EMPTY_MOVES
	// Animating drones are passed separately (`moving`) to DroneNodes, so `scene`
	// itself is identity-stable between selection/data changes.
	const scene: Scene = useMemo(
		() => ({
			hubs,
			drones,
			connections,
			origin: simulation.origin,
			destination: simulation.destination,
			selectedHubId,
			selectedConnectionId,
		}),
		[
			hubs,
			drones,
			connections,
			simulation.origin,
			simulation.destination,
			selectedHubId,
			selectedConnectionId,
		],
	)

	// Resolve selection by hit-testing the click point: a station box wins over a
	// connection track, and an empty click clears. Skipped right after a real drag
	// so panning never changes the selection.
	const handleStageClick = useCallback(
		(e: Konva.KonvaEventObject<MouseEvent>) => {
			if (wasDragging()) return
			const pointer = e.target.getStage()?.getPointerPosition()
			if (!pointer) return
			const hubId = hitTestHub(view, hubs, pointer.x, pointer.y)
			if (hubId) {
				setSelectedHubId(hubId)
				setSelectedConnectionId(null)
				return
			}
			const connId = hitTestConnection(view, scene, pointer.x, pointer.y)
			if (connId) {
				setSelectedConnectionId(connId)
				setSelectedHubId(null)
				return
			}
			setSelectedHubId(null)
			setSelectedConnectionId(null)
		},
		[view, hubs, scene, wasDragging],
	)

	const closeHub = useCallback(() => setSelectedHubId(null), [])
	const closeConnection = useCallback(() => setSelectedConnectionId(null), [])

	const selectedHub = hubs.get(selectedHubId ?? "")
	const selectedConnection = connections.get(selectedConnectionId ?? "")

	return (
		<div className='relative w-full h-full flex'>
			<div
				ref={containerRef}
				className='flex-1 bg-[#0a0a0a] cursor-grab active:cursor-grabbing'>
				<Stage
					width={view.canvasWidth}
					height={view.canvasHeight}
					onWheel={handleWheel}
					onMouseDown={handleMouseDown}
					onMouseMove={handleMouseMove}
					onMouseUp={endDrag}
					onMouseLeave={endDrag}
					onClick={handleStageClick}
					onTap={handleStageClick}>
					<Layer>
						<Background view={view} />
						{connEntries.map(([connId, connection]) => (
							<ConnectionShape
								key={connId}
								view={view}
								scene={scene}
								connId={connId}
								connection={connection}
							/>
						))}
						{hubEntries.map(([hubId, hub]) => (
							<HubShape
								key={hubId}
								view={view}
								scene={scene}
								hubId={hubId}
								hub={hub}
							/>
						))}
						<DroneNodes
							view={view}
							scene={scene}
							moving={moving}
							getColor={getDroneColorRef.current}
						/>
					</Layer>
				</Stage>
			</div>

			<CanvasToolbar
				scale={view.scale}
				onFit={autoFit}
				onZoomIn={zoomIn}
				onZoomOut={zoomOut}
			/>

			{selectedHub && (
				<HubDetailPanel
					hub={selectedHub}
					onClose={closeHub}
				/>
			)}

			{selectedConnection && (
				<ConnectionDetailPanel
					connection={selectedConnection}
					hubs={hubs}
					drones={drones}
					onClose={closeConnection}
				/>
			)}
		</div>
	)
}
