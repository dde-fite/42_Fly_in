import { describe, expect, it } from "vitest"
import type { Hub } from "../../types/simulation"
import {
	computeAutoFit,
	HUB_SPACING,
	MAX_SCALE,
	MIN_SCALE,
	modelToCanvas,
	type View,
	zoomAt,
} from "./view"

const view: View = {
	scale: 100,
	panX: 50,
	panY: 50,
	canvasWidth: 800,
	canvasHeight: 600,
}

const hub = (x: number, y: number): Hub => ({
	name: "H",
	position: [x, y],
	access: "open",
	connections: [],
	capacity: 1,
	drones: [],
})

describe("modelToCanvas", () => {
	it("applies hub spacing, scale and pan", () => {
		const [x, y] = modelToCanvas(view, 1, 2)
		expect(x).toBeCloseTo(1 * HUB_SPACING * 100 + 50)
		expect(y).toBeCloseTo(2 * HUB_SPACING * 100 + 50)
	})
})

describe("zoomAt", () => {
	it("keeps the model point under the anchor pinned", () => {
		const next = zoomAt(view, 300, 200, 2)
		const before = (300 - view.panX) / view.scale
		const after = (300 - next.panX) / next.scale
		expect(after).toBeCloseTo(before)
	})

	it("clamps scale to the configured limits", () => {
		expect(zoomAt(view, 0, 0, 1000).scale).toBe(MAX_SCALE)
		expect(zoomAt(view, 0, 0, 0.0001).scale).toBe(MIN_SCALE)
	})
})

describe("computeAutoFit", () => {
	it("returns null when there are no hubs", () => {
		expect(computeAutoFit(new Map(), 800, 600)).toBeNull()
	})

	it("frames the hubs centred and capped at scale 200", () => {
		const hubs = new Map<string, Hub>([
			["a", hub(0, 0)],
			["b", hub(2, 0)],
		])
		const fit = computeAutoFit(hubs, 800, 600)
		expect(fit).not.toBeNull()
		expect(fit?.scale).toBeCloseTo(188.235, 2)
		expect(fit?.panX).toBeCloseTo(80, 2)
		expect(fit?.panY).toBeCloseTo(205.882, 2)
	})
})
