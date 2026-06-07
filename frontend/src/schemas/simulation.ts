import { z } from 'zod'
import { HubSchema } from './hub'
import { ConnectionSchema } from './connection'
import { DroneSchema } from './drone'

export const SimulationSchema = z.object({
    turn: z.number(),
    hubs: z.record(z.string(), HubSchema),
    origin: z.uuidv4(),
    destination: z.uuidv4(),
    connections: z.record(z.string(), ConnectionSchema),
    drones: z.record(z.string(), DroneSchema),
})