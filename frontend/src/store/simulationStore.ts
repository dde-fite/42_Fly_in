import { create } from "zustand";
import { SimulationData } from "../types/simulation";

interface SimulationStore {
	simulation: SimulationData | null;
	setSimulation: (data: SimulationData) => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => {
	return {
		simulation: null,

		setSimulation: (simulation: SimulationData) => set(() => ({ simulation })),
	};
});
