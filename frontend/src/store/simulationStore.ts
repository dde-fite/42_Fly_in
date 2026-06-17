import { create } from "zustand"
import {
	advanceSimulation as apiAdvanceSimulation,
	createSimulation,
} from "../services/api"
import type { Simulation } from "../types/simulation"
import { useSessionStore } from "./sessionStore"

interface SimulationStore {
	simulation: Simulation | null
	fitViewTrigger: number
	newSimulation: (data: File) => Promise<void>
	setSimulation: (data: Simulation | null) => void
	clearSimulation: () => void
	advanceSimulation: (steps: number) => Promise<void>
	requestFitView: () => void
}

// Run a simulation-producing request with shared loading/error handling.
async function loadSimulation(
	set: (state: { simulation: Simulation }) => void,
	run: () => Promise<Simulation>,
) {
	const session = useSessionStore.getState()
	session.setIsLoading(true)
	try {
		const simulation = await run()
		session.setError(null)
		set({ simulation })
	} catch (e) {
		session.setError(e instanceof Error ? e.message : "Unknown error")
	} finally {
		session.setIsLoading(false)
	}
}

export const useSimulationStore = create<SimulationStore>(set => ({
	simulation: null,
	fitViewTrigger: 0,

	newSimulation: (data: File) =>
		loadSimulation(set, () => createSimulation(data)),

	setSimulation: (simulation: Simulation | null) => set({ simulation }),

	clearSimulation: () => set({ simulation: null }),

	advanceSimulation: (steps: number) =>
		loadSimulation(set, () => apiAdvanceSimulation(steps)),

	requestFitView: () =>
		set(state => ({ fitViewTrigger: state.fitViewTrigger + 1 })),
}))
