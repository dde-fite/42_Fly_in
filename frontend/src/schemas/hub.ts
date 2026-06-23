import { z } from "zod"

export const HubSchema = z.object({
	name: z.string(),
	position: z.tuple([z.number(), z.number()]),
	access: z.string(),
	color: z.optional(z.string()),
	connections: z.array(z.uuidv4()),
	capacity: z.number(),
	drones: z.array(z.uuidv4()),
})
