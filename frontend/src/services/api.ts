import { ConnectionSchema } from "../schemas/connection";
import { DroneSchema } from "../schemas/drone";
import { HubSchema } from "../schemas/hub";
import { TokenSchema } from "../schemas/token";
import { useSessionStore } from "../store/sessionStore";
import type { ResponseSimulation, Token } from "../types/api";
import type { Connection, Drone, Hub } from "../types/simulation";

const API_BASE = `${import.meta.env.VITE_BACKEND_URL}/api`;

export async function generateToken(): Promise<Token> {
	const response = await fetch(`${API_BASE}/token`);
	if (!response.ok) {
		throw new Error("Failed to generate token");
	}
	const data = await response.json();
	return TokenSchema.parse(data);
}

export async function createSimulation(
	file: File,
): Promise<ResponseSimulation> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	const formData = new FormData();
	formData.append("file", file);

	const response = await fetch(
		`${API_BASE}/simulation?token=${encodeURIComponent(token)}`,
		{
			method: "POST",
			body: formData,
		},
	);

	if (!response.ok) {
		const error = await response.text();
		throw new Error(`Failed to create simulation: ${error}`);
	}

	return response.json();
}

export async function getSimulation(): Promise<ResponseSimulation> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	const response = await fetch(
		`${API_BASE}/simulation?token=${encodeURIComponent(token)}`,
	);

	if (!response.ok) {
		throw new Error("Simulation not found");
	}

	return response.json();
}

export async function advanceSimulation(
	steps: number = 1,
): Promise<ResponseSimulation> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	const response = await fetch(
		`${API_BASE}/simulation/step?token=${encodeURIComponent(token)}&steps=${steps}`,
		{ method: "POST" },
	);

	if (!response.ok) {
		throw new Error("Failed to advance simulation");
	}

	return response.json();
}

export async function getHub(ids: string[]): Promise<Hub> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	let url = `${API_BASE}/hub?token=${encodeURIComponent(token)}`;
	ids.forEach((id) => {
		url += `&id=${encodeURIComponent(id)}`;
	});
	const response = await fetch(url);
	if (!response.ok) {
		throw new Error("Hub not found");
	}
	const data = await response.json();
	return HubSchema.parse(data);
}

export async function getDrone(ids: string[]): Promise<Drone> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	let url = `${API_BASE}/drone?token=${encodeURIComponent(token)}`;
	ids.forEach((id) => {
		url += `&id=${encodeURIComponent(id)}`;
	});
	const response = await fetch(url);
	if (!response.ok) {
		throw new Error("Drone not found");
	}
	const data = await response.json();
	return DroneSchema.parse(data);
}

export async function getConnection(ids: string[]): Promise<Connection> {
	const token = useSessionStore((state) => state.token);
	if (!token) {
		throw new Error(`Token is null`);
	}
	let url = `${API_BASE}/connection?token=${encodeURIComponent(token)}`;
	ids.forEach((id) => {
		url += `&id=${encodeURIComponent(id)}`;
	});
	const response = await fetch(url);
	if (!response.ok) {
		throw new Error("Connection not found");
	}
	const data = await response.json();
	return ConnectionSchema.parse(data);
}
