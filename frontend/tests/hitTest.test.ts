import { describe, expect, it } from "vitest"
import { hitTestConnection, hitTestHub } from "../src/canvas/hitTest"
import type { Scene } from "../src/canvas/scene"
import { HUB_SPACING, type View } from "../src/canvas/view"
import type { Hub } from "../src/types/simulation"

const view: View = {
	scale: 100,
	panX: 50,
	panY: 50,
	canvasWidth: 800,
	canvasHeight: 600,
}

const hub = (name: string, x: number, y: number): Hub => ({
	name,
	position: [x, y],
	access: "open",
	connections: [],
	capacity: 1,
	drones: [],
})

// Canvas coordinate of model point (mx, my).
const toCanvas = (mx: number, my: number) => ({
	x: mx * HUB_SPACING * view.scale + view.panX,
	y: my * HUB_SPACING * view.scale + view.panY,
})

describe("hitTestHub", () => {
	const hubs = new Map([
		["hub-a", hub("A", 0, 0)],
		["hub-b", hub("B", 1, 0)],
	])

	it("returns hub id when click is inside station box", () => {
		const { x, y } = toCanvas(0, 0)
		expect(hitTestHub(view, hubs, x, y)).toBe("hub-a")
	})

	it("returns null when click is far from all hubs", () => {
		expect(hitTestHub(view, hubs, 0, 0)).toBeNull()
	})

	it("distinguishes between two adjacent hubs", () => {
		const a = toCanvas(0, 0)
		const b = toCanvas(1, 0)
		expect(hitTestHub(view, hubs, a.x, a.y)).toBe("hub-a")
		expect(hitTestHub(view, hubs, b.x, b.y)).toBe("hub-b")
		expect(hitTestHub(view, hubs, a.x, a.y)).not.toBe("hub-b")
	})
})

describe("hitTestConnection", () => {
	const scene: Scene = {
		hubs: new Map([
			["hub-a", hub("A", 0, 0)],
			["hub-b", hub("B", 1, 0)],
		]),
		drones: new Map(),
		connections: new Map([
			[
				"conn-ab",
				{
					name: "A-B",
					hubs: ["hub-a", "hub-b"],
					capacity: 1,
				},
			],
		]),
		origin: "hub-a",
		destination: "hub-b",
		selectedHubId: null,
		selectedConnectionId: null,
	}

	it("returns connection id when click is on the track midpoint", () => {
		const mid = toCanvas(0.5, 0)
		expect(hitTestConnection(view, scene, mid.x, mid.y)).toBe("conn-ab")
	})

	it("returns null when click is far from all connections", () => {
		expect(hitTestConnection(view, scene, 0, 0)).toBeNull()
	})

	it("returns null when connections map is empty", () => {
		const emptyScene: Scene = { ...scene, connections: new Map() }
		const mid = toCanvas(0.5, 0)
		expect(hitTestConnection(view, emptyScene, mid.x, mid.y)).toBeNull()
	})
})
