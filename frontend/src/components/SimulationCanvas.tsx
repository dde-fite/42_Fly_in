import type Konva from "konva"
import {
	useCallback,
	useEffect,
	useMemo,
	useReducer,
	useRef,
	useState,
} from "react"
import { Layer, Stage } from "react-konva"
import { createDroneColorCache } from "../canvas/colors"
import { hitTestConnection, hitTestHub } from "../canvas/hitTest"
import { isRainbow } from "../canvas/palette"
import type { DroneMove, Scene } from "../canvas/scene"
import { computeAutoFit, type View, zoomAt } from "../canvas/view"
import { useDroneAnimation } from "../hooks/useDroneAnimation"
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

// Pointer travel (px) before a press counts as a pan instead of a click.
const DRAG_THRESHOLD = 4

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

	const [view, setView] = useState<View>({
		scale: 100,
		panX: 50,
		panY: 50,
		canvasWidth: 800,
		canvasHeight: 600,
	})

	// Drag (pan) state kept in a ref so panning doesn't thrash React state on the
	// start coordinates. `moved` flips once the pointer passes DRAG_THRESHOLD, so
	// a click with tiny jitter pans nothing and still selects cleanly.
	const dragRef = useRef({
		active: false,
		moved: false,
		x: 0,
		y: 0,
		startX: 0,
		startY: 0,
	})
	const hasAutoFittedRef = useRef(false)

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

	const autoFit = useCallback(() => {
		setView(v => {
			const fit = computeAutoFit(hubs, v.canvasWidth, v.canvasHeight)
			return fit ? { ...v, ...fit } : v
		})
	}, [hubs])

	// First auto-fit once stations exist.
	useEffect(() => {
		if (!hasAutoFittedRef.current && hubs.size > 0) {
			hasAutoFittedRef.current = true
			autoFit()
		}
	}, [hubs, autoFit])

	// Manual "fit view" requests from the menu/keyboard.
	const fitViewTrigger = useSimulationStore(state => state.fitViewTrigger)
	const prevFitTriggerRef = useRef(0)
	useEffect(() => {
		if (fitViewTrigger === prevFitTriggerRef.current) return
		prevFitTriggerRef.current = fitViewTrigger
		if (fitViewTrigger === 0) return
		autoFit()
	}, [fitViewTrigger, autoFit])

	// Track the container size so the Stage matches its parent.
	useEffect(() => {
		const el = containerRef.current
		if (!el) return
		const measure = () =>
			setView(v => ({
				...v,
				canvasWidth: el.clientWidth,
				canvasHeight: el.clientHeight,
			}))
		measure()
		const observer = new ResizeObserver(measure)
		observer.observe(el)
		return () => observer.disconnect()
	}, [])

	// Keep redrawing while any hub uses the animated "rainbow" colour so its hue
	// cycles over time. Idle (no rainbow hub) leaves the canvas static.
	const hasRainbow = useMemo(
		() => Array.from(hubs.values()).some(h => isRainbow(h.color)),
		[hubs],
	)
	useEffect(() => {
		if (!hasRainbow) return
		let raf = requestAnimationFrame(function tick() {
			bumpRender()
			raf = requestAnimationFrame(tick)
		})
		return () => cancelAnimationFrame(raf)
		// bumpRender (useReducer dispatch) is stable; omitted intentionally.
	}, [hasRainbow])

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

	const handleWheel = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
		e.evt.preventDefault()
		const pointer = e.target.getStage()?.getPointerPosition()
		if (!pointer) return
		// Exponential factor: smooth and direction-symmetric across wheel/trackpad.
		const factor = Math.exp(-e.evt.deltaY * 0.0015)
		setView(v => zoomAt(v, pointer.x, pointer.y, factor))
	}, [])

	const handleMouseDown = useCallback(
		(e: Konva.KonvaEventObject<MouseEvent>) => {
			if (e.evt.button !== 0) return
			dragRef.current = {
				active: true,
				moved: false,
				x: e.evt.clientX,
				y: e.evt.clientY,
				startX: e.evt.clientX,
				startY: e.evt.clientY,
			}
		},
		[],
	)

	const handleMouseMove = useCallback(
		(e: Konva.KonvaEventObject<MouseEvent>) => {
			const drag = dragRef.current
			if (!drag.active) return
			// Ignore sub-threshold jitter so a plain click never pans (which would
			// move the scene out from under the pointer and break selection).
			if (
				!drag.moved &&
				Math.hypot(e.evt.clientX - drag.startX, e.evt.clientY - drag.startY) <
					DRAG_THRESHOLD
			)
				return
			drag.moved = true
			const dx = e.evt.clientX - drag.x
			const dy = e.evt.clientY - drag.y
			drag.x = e.evt.clientX
			drag.y = e.evt.clientY
			setView(v => ({ ...v, panX: v.panX + dx, panY: v.panY + dy }))
		},
		[],
	)

	const endDrag = useCallback(() => {
		dragRef.current.active = false
	}, [])

	// Resolve selection by hit-testing the click point: a station box wins over a
	// connection track, and an empty click clears. Skipped right after a real drag
	// so panning never changes the selection.
	const handleStageClick = useCallback(
		(e: Konva.KonvaEventObject<MouseEvent>) => {
			if (dragRef.current.moved) return
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
		[view, hubs, scene],
	)

	// Zoom buttons (toolbar) zoom around the canvas centre.
	const zoomByFactor = useCallback(
		(factor: number) =>
			setView(v => zoomAt(v, v.canvasWidth / 2, v.canvasHeight / 2, factor)),
		[],
	)
	const zoomIn = useCallback(() => zoomByFactor(1.2), [zoomByFactor])
	const zoomOut = useCallback(() => zoomByFactor(1 / 1.2), [zoomByFactor])
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
