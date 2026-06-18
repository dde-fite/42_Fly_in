import { randomUUID } from "node:crypto"
import { describe, expect, it } from "vitest"
import { ConnectionSchema } from "./connection"
import { DroneSchema } from "./drone"
import { HubSchema } from "./hub"
import { RawSimulationSchema, SimulationSchema } from "./simulation"
import { TokenSchema } from "./token"

const uuid = () => randomUUID()

describe("HubSchema", () => {
	it("accepts a well-formed hub", () => {
		const hub = {
			name: "Alpha",
			position: [1, 2],
			access: "open",
			connections: [uuid()],
			capacity: 3,
			drones: [uuid()],
		}
		expect(HubSchema.parse(hub)).toMatchObject({ name: "Alpha", capacity: 3 })
	})

	it("rejects a malformed position", () => {
		expect(() =>
			HubSchema.parse({
				name: "x",
				position: [1],
				access: "o",
				connections: [],
				capacity: 1,
				drones: [],
			}),
		).toThrow()
	})
})

describe("ConnectionSchema", () => {
	it("accepts a connection between two hubs", () => {
		const c = ConnectionSchema.parse({
			name: "c",
			hubs: ["a", "b"],
			capacity: 2,
		})
		expect(c.capacity).toBe(2)
	})
})

describe("DroneSchema", () => {
	it("accepts a drone with uuid location and destination", () => {
		const d = { name: "d", location: uuid(), destination: uuid() }
		expect(DroneSchema.parse(d)).toMatchObject({ name: "d" })
	})
})

describe("TokenSchema", () => {
	it("accepts a base64url token", () => {
		expect(TokenSchema.parse("SGVsbG8")).toBe("SGVsbG8")
	})

	it("rejects non-base64url characters", () => {
		expect(() => TokenSchema.parse("not a token!!")).toThrow()
	})
})

describe("RawSimulationSchema / SimulationSchema", () => {
	it("parses the raw backend shape (uuid arrays)", () => {
		const raw = {
			turn: 0,
			hubs: [uuid()],
			origin: uuid(),
			destination: uuid(),
			connections: [uuid()],
			drones: [uuid()],
		}
		expect(RawSimulationSchema.parse(raw).turn).toBe(0)
	})

	it("parses the enriched shape (records of objects)", () => {
		const id = uuid()
		const sim = {
			turn: 1,
			origin: id,
			destination: id,
			hubs: {
				[id]: {
					name: "h",
					position: [0, 0],
					access: "o",
					connections: [],
					capacity: 1,
					drones: [],
				},
			},
			connections: { [id]: { name: "c", hubs: [id, id], capacity: 1 } },
			drones: { [id]: { name: "d", location: id, destination: id } },
		}
		expect(SimulationSchema.parse(sim).turn).toBe(1)
	})
})
