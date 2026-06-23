import { create } from "zustand"
import {
	advanceSimulation as apiAdvanceSimulation,
	createSimulation,
} from "../services/api"
import type { Simulation } from "../types/simulation"
import { useSessionStore } from "./sessionStore"

interface SimulationStore {
	simulation: Simulation | null
	// Monotonic turn counter. Only `advanceSimulation` moves it forward (by the
	// number of steps requested); a new/replaced/cleared simulation resets it to
	// 0. The drone-move animation glides only on a single forward step
	// (delta === 1), so restarts and multi-step jumps never play a phantom glide.
	turn: number
	fitViewTrigger: number
	// Current playback multiplier (0 paused, 1 play, >1 fast). Drives how fast
	// the drone-move animation plays so it always finishes before the next turn.
	playbackSpeed: number
	newSimulation: (data: File) => Promise<void>
	setSimulation: (data: Simulation | null) => void
	clearSimulation: () => void
	advanceSimulation: (steps: number) => Promise<void>
	requestFitView: () => void
	setPlaybackSpeed: (speed: number) => void
}

// Run a simulation-producing request with shared loading/error handling. `apply`
// commits the result, letting each caller decide how the turn counter moves.
async function loadSimulation(
	run: () => Promise<Simulation>,
	apply: (simulation: Simulation) => void,
) {
	const session = useSessionStore.getState()
	session.setIsLoading(true)
	try {
		const simulation = await run()
		session.setError(null)
		apply(simulation)
	} catch (e) {
		session.setError(e instanceof Error ? e.message : "Unknown error")
	} finally {
		session.setIsLoading(false)
	}
}

export const useSimulationStore = create<SimulationStore>(set => ({
	simulation: null,
	turn: 0,
	fitViewTrigger: 0,
	playbackSpeed: 1,

	newSimulation: (data: File) =>
		loadSimulation(
			() => createSimulation(data),
			simulation => set({ simulation, turn: 0 }),
		),

	setSimulation: (simulation: Simulation | null) =>
		set({ simulation, turn: 0 }),

	clearSimulation: () => set({ simulation: null, turn: 0 }),

	advanceSimulation: (steps: number) =>
		loadSimulation(
			() => apiAdvanceSimulation(steps),
			simulation => set(state => ({ simulation, turn: state.turn + steps })),
		),

	requestFitView: () =>
		set(state => ({ fitViewTrigger: state.fitViewTrigger + 1 })),

	setPlaybackSpeed: (speed: number) => set({ playbackSpeed: speed }),
}))
