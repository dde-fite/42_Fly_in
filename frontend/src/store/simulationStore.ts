import { create } from "zustand";
import type { SimulationData } from "../types/simulation";
import type { Token } from "../types/api";

interface SimulationStore {
	simulation: SimulationData | null;
	token: Token | null;
	setSimulation: (data: SimulationData | null) => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => {
	return {
		simulation: null,

		newSimulation: (token: Token, file: File) =>
		setSimulation: (simulation: SimulationData | null) => set(() => ({ simulation }))
	};
});
