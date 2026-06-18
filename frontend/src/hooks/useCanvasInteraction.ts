import { type MutableRefObject, type RefObject, useCallback } from "react"
import { hitTestConnection, hitTestHub } from "../lib/canvas/hitTest"
import { zoomAt } from "../lib/canvas/view"
import type { Connection, Hub } from "../types/simulation"

// Mutable view + drag state shared with the renderer (a ref so handlers never
// trigger a React re-render while panning or zooming).
export interface CanvasState {
	scale: number
	panX: number
	panY: number
	canvasWidth: number
	canvasHeight: number
	isDragging: boolean
	dragStartX: number
	dragStartY: number
	hasAutoFitted: boolean
}

interface Options {
	canvasRef: RefObject<HTMLCanvasElement | null>
	stateRef: MutableRefObject<CanvasState>
	hubs: Map<string, Hub>
	connections: Map<string, Connection>
	redraw: () => void
	autoFit: (hubs: Map<string, Hub>) => void
	onSelectHub: (id: string | null) => void
	onSelectConnection: (id: string | null) => void
}

// Canvas pointer, wheel, zoom-button, fit and resize handlers. All viewport
// mutation lives in `stateRef` and is followed by a redraw; click selection is
// reported back through the onSelect callbacks. Returns the handler set to wire
// onto the <canvas> and toolbar.
export function useCanvasInteraction({
	canvasRef,
	stateRef,
	hubs,
	connections,
	redraw,
	autoFit,
	onSelectHub,
	onSelectConnection,
}: Options) {
	const handleCanvasClick = useCallback(
		(e: React.MouseEvent<HTMLCanvasElement>) => {
			const canvas = canvasRef.current
			if (!canvas) return
			const rect = canvas.getBoundingClientRect()
			const canvasX = e.clientX - rect.left
			const canvasY = e.clientY - rect.top

			const hubId = hitTestHub(stateRef.current, hubs, canvasX, canvasY)
			if (hubId) {
				onSelectHub(hubId)
				onSelectConnection(null)
				return
			}
			const connId = hitTestConnection(
				stateRef.current,
				hubs,
				connections,
				canvasX,
				canvasY,
			)
			if (connId) {
				onSelectConnection(connId)
				onSelectHub(null)
				return
			}
			onSelectHub(null)
			onSelectConnection(null)
		},
		[canvasRef, stateRef, hubs, connections, onSelectHub, onSelectConnection],
	)

	const handleWheel = useCallback(
		(e: React.WheelEvent<HTMLCanvasElement>) => {
			e.preventDefault()
			const canvas = canvasRef.current
			if (!canvas) return
			const rect = canvas.getBoundingClientRect()
			const anchorX = e.clientX - rect.left
			const anchorY = e.clientY - rect.top
			// Exponential factor: smooth and direction-symmetric across wheel/trackpad.
			const factor = Math.exp(-e.deltaY * 0.0015)
			const next = zoomAt(stateRef.current, anchorX, anchorY, factor)
			stateRef.current.scale = next.scale
			stateRef.current.panX = next.panX
			stateRef.current.panY = next.panY
			redraw()
		},
		[canvasRef, stateRef, redraw],
	)

	const handleMouseDown = useCallback(
		(e: React.MouseEvent<HTMLCanvasElement>) => {
			if (e.button !== 0) return
			stateRef.current.isDragging = true
			stateRef.current.dragStartX = e.clientX
			stateRef.current.dragStartY = e.clientY
		},
		[stateRef],
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
		[stateRef, redraw],
	)

	const handleMouseUp = useCallback(() => {
		stateRef.current.isDragging = false
	}, [stateRef])

	const handleResize = useCallback(() => {
		const canvas = canvasRef.current
		if (!canvas?.parentElement) return
		stateRef.current.canvasWidth = canvas.parentElement.clientWidth
		stateRef.current.canvasHeight = canvas.parentElement.clientHeight
		canvas.width = stateRef.current.canvasWidth
		canvas.height = stateRef.current.canvasHeight
		redraw()
	}, [canvasRef, stateRef, redraw])

	const handleFit = useCallback(() => {
		autoFit(hubs)
		redraw()
	}, [hubs, autoFit, redraw])

	// Zoom in/out around the canvas centre (toolbar buttons).
	const zoomByFactor = useCallback(
		(factor: number) => {
			const { canvasWidth, canvasHeight } = stateRef.current
			const next = zoomAt(
				stateRef.current,
				canvasWidth / 2,
				canvasHeight / 2,
				factor,
			)
			stateRef.current.scale = next.scale
			stateRef.current.panX = next.panX
			stateRef.current.panY = next.panY
			redraw()
		},
		[stateRef, redraw],
	)
	const handleZoomIn = useCallback(() => zoomByFactor(1.2), [zoomByFactor])
	const handleZoomOut = useCallback(() => zoomByFactor(1 / 1.2), [zoomByFactor])

	return {
		handleCanvasClick,
		handleWheel,
		handleMouseDown,
		handleMouseMove,
		handleMouseUp,
		handleResize,
		handleFit,
		handleZoomIn,
		handleZoomOut,
	}
}
