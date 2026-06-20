import { describe, expect, it } from "vitest"
import { droneSizeFor, getHubBox, railMetrics } from "../src/canvas/geometry"

describe("railMetrics", () => {
	it("scales spacing and width linearly with the view scale", () => {
		const m = railMetrics(100)
		expect(m.trackSpacing).toBeCloseTo(9)
		expect(m.railWidth).toBeCloseTo(3)
	})
})

describe("droneSizeFor", () => {
	it("is the drone fraction of the scale", () => {
		expect(droneSizeFor(100)).toBeCloseTo(9)
	})
})

describe("getHubBox", () => {
	it("computes dimensions for a single-capacity hub", () => {
		const box = getHubBox("AB", 100, 1)
		expect(box.fontSize).toBeCloseTo(14)
		expect(box.platformH).toBeCloseTo(5)
		expect(box.stationTrackSpacing).toBeCloseTo(22)
		expect(box.innerH).toBeCloseTo(22)
		expect(box.boxH).toBeCloseTo(36.4)
		expect(box.boxW).toBeCloseTo(38) // 0.1*2 + 0.18 = 0.38 units
	})

	it("grows height with capacity", () => {
		const box = getHubBox("AB", 100, 3)
		expect(box.innerH).toBeCloseTo(66)
		expect(box.boxH).toBeCloseTo(80.4)
	})

	it("clamps width to the minimum for short names", () => {
		expect(getHubBox("A", 100, 1).boxW).toBeCloseTo(34) // min 0.34 units
	})
})
