import { ConnectionSchema } from "../schemas/connection"
import { DroneSchema } from "../schemas/drone"
import { HubSchema } from "../schemas/hub"
import { RawSimulationSchema, SimulationSchema } from "../schemas/simulation"
import { TokenSchema } from "../schemas/token"
import { useSessionStore } from "../store/sessionStore"
import type { Token } from "../types/api"
import type { Connection, Drone, Hub, Simulation } from "../types/simulation"

const API_BASE = `${import.meta.env.VITE_BACKEND_URL}/api`

export async function generateToken(): Promise<Token> {
	const response = await fetch(`${API_BASE}/token`)
	if (!response.ok) {
		throw new Error("Failed to generate token")
	}
	const data = await response.json()
	return TokenSchema.parse(data)
}

// ── Individual item fetches ───────────────────────────────────────────────────

async function fetchById<T>(
	resource: string,
	label: string,
	schema: { parse: (data: unknown) => T },
	token: Token,
	id: string,
): Promise<T> {
	const response = await fetch(
		`${API_BASE}/${resource}?token=${encodeURIComponent(token)}&id=${encodeURIComponent(id)}`,
	)
	if (!response.ok) throw new Error(`${label} ${id} not found`)
	return schema.parse(await response.json())
}

const fetchHubById = (token: Token, id: string): Promise<Hub> =>
	fetchById("hub", "Hub", HubSchema, token, id)

const fetchDroneById = (token: Token, id: string): Promise<Drone> =>
	fetchById("drone", "Drone", DroneSchema, token, id)

const fetchConnectionById = (token: Token, id: string): Promise<Connection> =>
	fetchById("connection", "Connection", ConnectionSchema, token, id)

// ── Enrichment ────────────────────────────────────────────────────────────────

async function enrichSimulation(
	token: Token,
	raw: {
		turn: number
		hubs: string[]
		origin: string
		destination: string
		connections: string[]
		drones: string[]
	},
): Promise<Simulation> {
	const [hubEntries, connectionEntries, droneEntries] = await Promise.all([
		Promise.all(
			raw.hubs.map(async id => [id, await fetchHubById(token, id)] as const),
		),
		Promise.all(
			raw.connections.map(
				async id => [id, await fetchConnectionById(token, id)] as const,
			),
		),
		Promise.all(
			raw.drones.map(
				async id => [id, await fetchDroneById(token, id)] as const,
			),
		),
	])

	return SimulationSchema.parse({
		turn: raw.turn,
		origin: raw.origin,
		destination: raw.destination,
		hubs: Object.fromEntries(hubEntries),
		connections: Object.fromEntries(connectionEntries),
		drones: Object.fromEntries(droneEntries),
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
		const error = await response.text()
		throw new Error(`Failed to create simulation: ${error}`)
	}

	const raw = RawSimulationSchema.parse(await response.json())
	return enrichSimulation(token, raw)
}

export async function advanceSimulation(steps = 1): Promise<Simulation> {
	const token = requireToken()

	const response = await fetch(
		`${API_BASE}/simulation/step?token=${encodeURIComponent(token)}&steps=${steps}`,
		{ method: "POST" },
	)
	if (!response.ok) throw new Error("Failed to advance simulation")

	const raw = RawSimulationSchema.parse(await response.json())
	return enrichSimulation(token, raw)
}
