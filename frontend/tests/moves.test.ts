import { describe, expect, it } from "vitest"
import { computeDroneMoves } from "../src/canvas/moves"
import type { Connection, Hub, Simulation } from "../src/types/simulation"

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
	it("returns a single-leg move for a neighbouring hub", () => {
		const moves = computeDroneMoves(
			sim({ d1: "a" }),
			sim({ d1: "b" }),
			hubs,
			connections,
		)
		expect(moves).toEqual([
			{ id: "d1", segments: [{ fromId: "a", toId: "b", tA: 0, tB: 0 }] },
		])
	})

	it("ignores drones that did not move", () => {
		expect(
			computeDroneMoves(sim({ d1: "a" }), sim({ d1: "a" }), hubs, connections),
		).toEqual([])
	})

	it("ignores moves with no connecting path", () => {
		expect(
			computeDroneMoves(sim({ d1: "a" }), sim({ d1: "b" }), hubs, new Map()),
		).toEqual([])
	})

	it("glides through intermediate hubs when the move is not direct", () => {
		const pathHubs = new Map<string, Hub>([
			["a", hub()],
			["b", hub()],
			["c", hub()],
		])
		const pathConns = new Map<string, Connection>([
			["ab", { name: "ab", hubs: ["a", "b"], capacity: 1 }],
			["bc", { name: "bc", hubs: ["b", "c"], capacity: 1 }],
		])
		// a and c are not directly connected: the move must step a -> b -> c.
		const moves = computeDroneMoves(
			sim({ d1: "a" }),
			sim({ d1: "c" }),
			pathHubs,
			pathConns,
		)
		expect(moves).toEqual([
			{
				id: "d1",
				segments: [
					{ fromId: "a", toId: "b", tA: 0, tB: 0 },
					{ fromId: "b", toId: "c", tA: 0, tB: 0 },
				],
			},
		])
	})

	it("stacks drones sharing a connection on distinct rows", () => {
		const moves = computeDroneMoves(
			sim({ d1: "a", d2: "a" }),
			sim({ d1: "b", d2: "b" }),
			hubs,
			connections,
		)
		expect(moves.map(m => m.segments[0].tA)).toEqual([0, 1])
	})

	it("assigns rows deterministically regardless of drone key order", () => {
		const rowsFor = (locations: Record<string, string>) =>
			new Map(
				computeDroneMoves(
					sim(Object.fromEntries(Object.keys(locations).map(id => [id, "a"]))),
					sim(locations),
					hubs,
					connections,
				).map(m => [m.id, m.segments[0].tA]),
			)
		// Same drones, opposite object insertion order -> same row per drone.
		expect(rowsFor({ d1: "b", d2: "b" })).toEqual(rowsFor({ d2: "b", d1: "b" }))
	})

	it("gives crossing drones distinct rows so they do not overlap", () => {
		const moves = computeDroneMoves(
			sim({ d1: "a", d2: "b" }),
			sim({ d1: "b", d2: "a" }),
			hubs,
			connections,
		)
		const rows = moves.map(m => m.segments[0].tA)
		expect(new Set(rows).size).toBe(rows.length)
	})
})
