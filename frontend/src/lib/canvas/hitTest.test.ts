import { describe, expect, it } from "vitest"
import type { Connection, Hub } from "../../types/simulation"
import { hitTestConnection, hitTestHub } from "./hitTest"
import { modelToCanvas, type View } from "./view"

const view: View = {
	scale: 100,
	panX: 0,
	panY: 0,
	canvasWidth: 800,
	canvasHeight: 600,
}

const hub = (x: number, y: number, capacity = 1): Hub => ({
	name: "H",
	position: [x, y],
	access: "open",
	connections: [],
	capacity,
	drones: [],
})

describe("hitTestHub", () => {
	const hubs = new Map<string, Hub>([
		["a", hub(0, 0)],
		["b", hub(2, 0)],
	])

	it("returns the hub whose box is under the point", () => {
		const [cx, cy] = modelToCanvas(view, 0, 0)
		expect(hitTestHub(view, hubs, cx, cy)).toBe("a")
	})

	it("returns null when the point misses every box", () => {
		expect(hitTestHub(view, hubs, 99999, 99999)).toBeNull()
	})
})

describe("hitTestConnection", () => {
	const hubs = new Map<string, Hub>([
		["a", hub(0, 0)],
		["b", hub(1, 0)],
	])
	const connections = new Map<string, Connection>([
		["c", { name: "c", hubs: ["a", "b"], capacity: 1 }],
	])

	it("returns the connection when the point lies on its track", () => {
		// Track runs from x≈17 to x≈153 at y≈0 (see track tests); midpoint ≈ (85, 0).
		expect(hitTestConnection(view, hubs, connections, 85, 0)).toBe("c")
	})

	it("returns null away from any track", () => {
		expect(hitTestConnection(view, hubs, connections, 85, 9999)).toBeNull()
	})
})
