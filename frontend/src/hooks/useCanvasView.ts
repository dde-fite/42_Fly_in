import type Konva from "konva"
import { type RefObject, useCallback, useEffect, useRef, useState } from "react"
import { computeAutoFit, type View, zoomAt } from "../canvas/view"
import { useSimulationStore } from "../store/simulationStore"
import type { Hub } from "../types/simulation"

// Pointer travel (px) before a press counts as a pan instead of a click.
const DRAG_THRESHOLD = 4

// Owns the viewport: pan/zoom transform, the Stage size, auto-fit, and the
// mouse/wheel handlers that drive panning and zooming. Selection lives in the
// component; `wasDragging` lets it skip the click that ends a real pan.
export function useCanvasView(
	hubs: Map<string, Hub>,
	containerRef: RefObject<HTMLDivElement>,
) {
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
	}, [containerRef])

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

	// Zoom buttons (toolbar) zoom around the canvas centre.
	const zoomByFactor = useCallback(
		(factor: number) =>
			setView(v => zoomAt(v, v.canvasWidth / 2, v.canvasHeight / 2, factor)),
		[],
	)
	const zoomIn = useCallback(() => zoomByFactor(1.2), [zoomByFactor])
	const zoomOut = useCallback(() => zoomByFactor(1 / 1.2), [zoomByFactor])

	// True while the last press has become a real pan, so selection can ignore
	// the click that ends it.
	const wasDragging = useCallback(() => dragRef.current.moved, [])

	return {
		view,
		autoFit,
		zoomIn,
		zoomOut,
		handleWheel,
		handleMouseDown,
		handleMouseMove,
		endDrag,
		wasDragging,
	}
}
