import { describe, expect, it } from "vitest"
import type { Hub } from "../src/types/simulation"
import { getHubBox } from "../src/canvas/geometry"
import { connectionTrackLine, stationTrackY, trackOffsets } from "../src/canvas/track"
import type { View } from "../src/canvas/view"

const view: View = {
	scale: 100,
	panX: 0,
	panY: 0,
	canvasWidth: 800,
	canvasHeight: 600,
}

const hub = (x: number, capacity = 1): Hub => ({
	name: "H",
	position: [x, 0],
	access: "open",
	connections: [],
	capacity,
	drones: [],
})

describe("trackOffsets", () => {
	it("centres a connection's tracks within each station", () => {
		expect(trackOffsets(3, 5, 1)).toEqual({ offA: 1, offB: 2 })
	})

	it("is zero when capacities match the connection", () => {
		expect(trackOffsets(2, 2, 2)).toEqual({ offA: 0, offB: 0 })
	})
})

describe("stationTrackY", () => {
	it("places track centres evenly below the box top", () => {
		const box = getHubBox("H", 100, 2)
		expect(stationTrackY(100, box, 0)).toBeCloseTo(89)
		expect(stationTrackY(100, box, 1)).toBeCloseTo(111)
	})
})

describe("connectionTrackLine", () => {
	it("exits each station on the edge facing the other", () => {
		const [a, b] = connectionTrackLine(view, hub(0), hub(1), 0, 0)
		// A is left of B: A exits on its right edge (+17px), B on its left (-17px).
		expect(a.x).toBeCloseTo(17)
		expect(b.x).toBeCloseTo(153)
		expect(a.x).toBeLessThan(b.x)
	})
})
