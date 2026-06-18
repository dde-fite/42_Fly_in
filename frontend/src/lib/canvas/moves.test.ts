import { describe, expect, it } from "vitest"
import type { Connection, Hub, Simulation } from "../../types/simulation"
import { computeDroneMoves } from "./moves"

const hub = (capacity = 1): Hub => ({
	name: "H",
	position: [0, 0],
	access: "open",
	connections: [],
	capacity,
	drones: [],
})

function sim(droneLocations: Record<string, string>): Simulation {
	const drones = Object.fromEntries(
		Object.entries(droneLocations).map(([id, location]) => [
			id,
			{ name: id, location, destination: "z" },
		]),
	)
	return {
		turn: 0,
		origin: "a",
		destination: "z",
		hubs: {},
		connections: {},
		drones,
	}
}

const hubs = new Map<string, Hub>([
	["a", hub(2)],
	["b", hub(2)],
])
const connections = new Map<string, Connection>([
	["c", { name: "c", hubs: ["a", "b"], capacity: 2 }],
])

describe("computeDroneMoves", () => {
	it("returns a move for a drone that changed hubs along a connection", () => {
		const moves = computeDroneMoves(
			sim({ d1: "a" }),
			sim({ d1: "b" }),
			hubs,
			connections,
		)
		expect(moves).toEqual([{ id: "d1", fromId: "a", toId: "b", tA: 0, tB: 0 }])
	})

	it("ignores drones that did not move", () => {
		expect(
			computeDroneMoves(sim({ d1: "a" }), sim({ d1: "a" }), hubs, connections),
		).toEqual([])
	})

	it("ignores moves with no connecting track", () => {
		expect(
			computeDroneMoves(sim({ d1: "a" }), sim({ d1: "b" }), hubs, new Map()),
		).toEqual([])
	})

	it("stacks drones sharing a connection on distinct rows", () => {
		const moves = computeDroneMoves(
			sim({ d1: "a", d2: "a" }),
			sim({ d1: "b", d2: "b" }),
			hubs,
			connections,
		)
		expect(moves.map(m => m.tA)).toEqual([0, 1])
	})
})
