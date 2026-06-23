import { z } from "zod"
import { ConnectionSchema } from "./connection"
import { DroneSchema } from "./drone"
import { HubSchema } from "./hub"

// What the backend actually returns (arrays of UUIDs)
export const RawSimulationSchema = z.object({
	turn: z.number(),
	hubs: z.array(z.uuidv4()),
	origin: z.uuidv4(),
	destination: z.uuidv4(),
	connections: z.array(z.uuidv4()),
	drones: z.array(z.uuidv4()),
})

// Enriched simulation with full objects (built after fetching each item)
export const SimulationSchema = z.object({
	turn: z.number(),
	hubs: z.record(z.string(), HubSchema),
	origin: z.uuidv4(),
	destination: z.uuidv4(),
	connections: z.record(z.string(), ConnectionSchema),
	drones: z.record(z.string(), DroneSchema),
})
