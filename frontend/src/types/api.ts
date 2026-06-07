import type { z } from "zod";
import type { TokenSchema } from "../schemas/token";

export type Token = z.infer<typeof TokenSchema>;

export interface ResponseHub {
	name: string;
	position: [number, number];
	access: string;
	color?: string;
	drones: string[];
	capacity: number;
	connections: string[];
}

export interface ResponseDrone {
	name: string;
	location: string;
	destination: string;
}

export interface ResponseConnection {
	name: string;
	hubs: [string, string];
	capacity: number;
}

export interface ResponseSimulation {
	turn: number;
	hubs: string[];
	origin: string;
	destination: string;
	connections: string[];
	drones: string[];
}
