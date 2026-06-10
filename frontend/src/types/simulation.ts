import { z } from 'zod';
import type { ConnectionSchema } from '../schemas/connection';
import type { DroneSchema } from '../schemas/drone';
import type { HubSchema } from '../schemas/hub';

export type Hub = z.infer<typeof HubSchema>;
export type Connection = z.infer<typeof ConnectionSchema>;
export type Drone = z.infer<typeof DroneSchema>;
