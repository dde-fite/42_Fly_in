import { z } from "zod"

export const DroneSchema = z.object({
	name: z.string(),
	location: z.uuidv4(),
	destination: z.uuidv4(),
})
