import { z } from "zod"

export const ConnectionSchema = z.object({
	name: z.string(),
	hubs: z.tuple([z.string(), z.string()]),
	capacity: z.number(),
})
