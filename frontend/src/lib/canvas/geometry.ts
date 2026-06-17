import type { Hub } from "../../types/simulation"

// Shared, capped rail metrics so the connection tracks and station tracks line
// up, and so boxes stop growing past a max pixel size (which lets zooming-in
// actually separate stations instead of growing them at the same rate).
export function railMetrics(scale: number) {
	const trackSpacing = Math.min(Math.max(7, scale * 0.11), 16)
	const railWidth = Math.min(Math.max(1, scale * 0.016), 2.4)
	return { trackSpacing, railWidth }
}

export function getHubBox(name: string, scale: number, capacity = 1) {
	const fontSize = Math.min(Math.max(8, scale * 0.1), 15)
	const { trackSpacing } = railMetrics(scale)
	const platformH = Math.min(Math.max(5, scale * 0.055), 9)
	const platformGap = Math.min(Math.max(2, scale * 0.025), 4)
	const innerH = trackSpacing * Math.max(1, capacity)
	const boxH = innerH + (platformH + platformGap) * 2
	const boxW = Math.max(64, fontSize * name.length * 0.72 + 36)
	return { boxW, boxH, fontSize, trackSpacing, platformH, platformGap, innerH }
}

// Smallest scale (≥ initialScale) at which no two hub boxes overlap, leaving a
// margin so the connecting tracks are clearly visible between stations.
export function fitSeparationScale(hubs: Hub[], initialScale: number): number {
	if (hubs.length < 2) return initialScale
	// Cap how far we are willing to zoom in to separate stations, so a pair that
	// can never be separated (coincident positions) does not lock the view at an
	// unusable zoom. Boxes are size-capped, so separation converges quickly.
	const MAX_SCALE = Math.max(initialScale, 2500)
	let scale = initialScale
	for (let iter = 0; iter < 60; iter++) {
		// Constant pixel margin so increasing scale always reduces overlap and the
		// connecting track stays clearly visible between stations.
		const margin = 60
		let overlap = false
		for (let i = 0; i < hubs.length && !overlap; i++) {
			const a = getHubBox(hubs[i].name, scale, hubs[i].capacity)
			for (let j = i + 1; j < hubs.length; j++) {
				const b = getHubBox(hubs[j].name, scale, hubs[j].capacity)
				const dx = Math.abs(hubs[i].position[0] - hubs[j].position[0]) * scale
				const dy = Math.abs(hubs[i].position[1] - hubs[j].position[1]) * scale
				const needX = (a.boxW + b.boxW) / 2 + margin
				const needY = (a.boxH + b.boxH) / 2 + margin
				if (dx < needX && dy < needY) {
					overlap = true
					break
				}
			}
		}
		if (!overlap) break
		scale *= 1.12
		if (scale >= MAX_SCALE) {
			scale = MAX_SCALE
			break
		}
	}
	return scale
}

// Point on rectangle edge from its center in direction (ux, uy)
export function rectEdge(
	cx: number,
	cy: number,
	w: number,
	h: number,
	ux: number,
	uy: number,
): [number, number] {
	const tx = Math.abs(ux) > 1e-9 ? w / 2 / Math.abs(ux) : Infinity
	const ty = Math.abs(uy) > 1e-9 ? h / 2 / Math.abs(uy) : Infinity
	const t = Math.min(tx, ty)
	return [cx + ux * t, cy + uy * t]
}
