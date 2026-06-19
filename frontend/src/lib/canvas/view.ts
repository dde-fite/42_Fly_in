import type { Hub } from "../../types/simulation"

// Viewport transform: model coordinates → canvas pixels.
export interface View {
	scale: number
	panX: number
	panY: number
	canvasWidth: number
	canvasHeight: number
}

// Distance multiplier between neighbouring stations. Station boxes are sized in
// fractions of `scale` (1 grid unit), but long names or high capacity can push a
// box past 1 unit, so stations 1 unit apart would touch. Spreading positions by
// this factor guarantees a gap and keeps the intermediate connections visible.
export const HUB_SPACING = 1.7

export function modelToCanvas(
	view: View,
	x: number,
	y: number,
): [number, number] {
	return [
		x * HUB_SPACING * view.scale + view.panX,
		y * HUB_SPACING * view.scale + view.panY,
	]
}

// Zoom limits, shared by wheel handler and any programmatic zoom.
export const MIN_SCALE = 5
export const MAX_SCALE = 8000

// Zoom the view by `factor` while keeping the model point under the cursor
// (anchorX, anchorY in canvas pixels) pinned in place — the visually intuitive
// "zoom toward the mouse" behaviour. Returns a new view; original untouched.
export function zoomAt(
	view: View,
	anchorX: number,
	anchorY: number,
	factor: number,
): View {
	const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, view.scale * factor))
	// Effective factor after clamping (so panning stays consistent at limits).
	const k = scale / view.scale
	return {
		...view,
		scale,
		panX: anchorX - (anchorX - view.panX) * k,
		panY: anchorY - (anchorY - view.panY) * k,
	}
}

export interface FitResult {
	scale: number
	panX: number
	panY: number
}

// Compute scale + pan that frames every hub, bumping zoom so stations don't
// overlap. Returns null when there are no hubs to frame.
export function computeAutoFit(
	hubs: Map<string, Hub>,
	canvasWidth: number,
	canvasHeight: number,
): FitResult | null {
	if (hubs.size === 0) return null

	let minX = Infinity,
		maxX = -Infinity
	let minY = Infinity,
		maxY = -Infinity

	for (const hub of hubs.values()) {
		const [x, y] = hub.position
		minX = Math.min(minX, x)
		maxX = Math.max(maxX, x)
		minY = Math.min(minY, y)
		maxY = Math.max(maxY, y)
	}

	// Bounding box in drawn units (positions are spread by HUB_SPACING).
	const width = (maxX - minX) * HUB_SPACING || 1
	const height = (maxY - minY) * HUB_SPACING || 1
	const padding = 80

	const scaleX = (canvasWidth - padding * 2) / width
	const scaleY = (canvasHeight - padding * 2) / height
	// Uniform camera: a single scale frames the whole graph. Stations scale with
	// it, so zoom is purely proportional and never needs an overlap "bump".
	const scale = Math.min(scaleX, scaleY, 200)

	return {
		scale,
		// Center the bounding box (overflows symmetrically if larger than viewport)
		panX: (canvasWidth - width * scale) / 2 - minX * HUB_SPACING * scale,
		panY: (canvasHeight - height * scale) / 2 - minY * HUB_SPACING * scale,
	}
}
