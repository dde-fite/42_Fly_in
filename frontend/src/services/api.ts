import { z } from "zod"
import { ConnectionSchema } from "../schemas/connection"
import { DroneSchema } from "../schemas/drone"
import { HubSchema } from "../schemas/hub"
import { RawSimulationSchema, SimulationSchema } from "../schemas/simulation"
import { TokenSchema } from "../schemas/token"
import { useSessionStore } from "../store/sessionStore"
import type { Token } from "../types/api"
import type { Simulation } from "../types/simulation"

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000"
const API_BASE = `${backendUrl}/api`

export async function generateToken(): Promise<Token> {
	const response = await fetch(`${API_BASE}/token`)
	if (!response.ok) {
		throw new Error("Failed to generate token")
	}
	const data = await response.json()
	return TokenSchema.parse(data)
}

// ── Bulk category fetches ─────────────────────────────────────────────────────

async function fetchAll<T>(
	resource: string,
	label: string,
	schema: z.ZodType<Record<string, T>>,
	token: Token,
): Promise<Record<string, T>> {
	const response = await fetch(
		`${API_BASE}/${resource}?token=${encodeURIComponent(token)}`,
	)
	if (!response.ok) throw new Error(`Failed to fetch ${label}`)
	return schema.parse(await response.json())
}

const HubsSchema = z.record(z.string(), HubSchema)
const ConnectionsSchema = z.record(z.string(), ConnectionSchema)
const DronesSchema = z.record(z.string(), DroneSchema)

// ── Enrichment ────────────────────────────────────────────────────────────────

async function enrichSimulation(
	token: Token,
	raw: {
		turn: number
		origin: string
		destination: string
	},
): Promise<Simulation> {
	const [hubs, connections, drones] = await Promise.all([
		fetchAll("hubs", "hubs", HubsSchema, token),
		fetchAll("connections", "connections", ConnectionsSchema, token),
		fetchAll("drones", "drones", DronesSchema, token),
	])

	return SimulationSchema.parse({
		turn: raw.turn,
		origin: raw.origin,
		destination: raw.destination,
		hubs,
		connections,
		drones,
	})
}

// ── Public API ────────────────────────────────────────────────────────────────

function requireToken(): Token {
	const token = useSessionStore.getState().token
	if (!token) throw new Error("Token is null")
	return token
}

export async function createSimulation(file: File): Promise<Simulation> {
	const token = requireToken()

	const formData = new FormData()
	formData.append("file", file)

	const response = await fetch(
		`${API_BASE}/simulation?token=${encodeURIComponent(token)}`,
		{ method: "POST", body: formData },
	)
	if (!response.ok) {
		const error = await response.text().catch(() => "")
		throw new Error(`Failed to create simulation: ${error}`)
	}

	const raw = RawSimulationSchema.parse(await response.json())
	return enrichSimulation(token, raw)
}

export async function advanceSimulation(steps = 1): Promise<Simulation> {
	if (steps < 1) throw new Error("steps must be >= 1")
	const token = requireToken()

	const response = await fetch(
		`${API_BASE}/simulation/step?token=${encodeURIComponent(token)}&steps=${steps}`,
		{ method: "POST" },
	)
	if (!response.ok) throw new Error("Failed to advance simulation")

	const raw = RawSimulationSchema.parse(await response.json())
	return enrichSimulation(token, raw)
}
