import type { Hub } from "../../types/simulation"
import { fitSeparationScale } from "./geometry"

// Viewport transform: model coordinates → canvas pixels.
export interface View {
	scale: number
	panX: number
	panY: number
	canvasWidth: number
	canvasHeight: number
}

export function modelToCanvas(
	view: View,
	x: number,
	y: number,
): [number, number] {
	return [x * view.scale + view.panX, y * view.scale + view.panY]
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

	const width = maxX - minX || 1
	const height = maxY - minY || 1
	const padding = 80

	const scaleX = (canvasWidth - padding * 2) / width
	const scaleY = (canvasHeight - padding * 2) / height
	const fitScale = Math.min(scaleX, scaleY, 200)

	// Bump scale up if stations would overlap at the fit scale
	const scale = fitSeparationScale([...hubs.values()], fitScale)

	return {
		scale,
		// Center the bounding box (overflows symmetrically if larger than viewport)
		panX: (canvasWidth - width * scale) / 2 - minX * scale,
		panY: (canvasHeight - height * scale) / 2 - minY * scale,
	}
}
