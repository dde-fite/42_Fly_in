import { create } from "zustand";
import { generateToken } from "../services/api";
import type { Token } from "../types/api";

interface SessionStore {
	token: Token | null;
	isLoading: boolean;
	error: string | null;
	setError: (error: string | null) => null;
	setIsLoading: (isLoading: boolean) => null;
	fetchToken: () => null;
}

export const useSessionStore = create<SessionStore>((set, get) => {
	return {
		token: null,
		isLoading: false,
		error: null,

		setError: (error: string | null) => set(() => ({ error })),
		setIsLoading: (isLoading: boolean) => set(() => ({ isLoading })),
		fetchToken: async () => {
			try {
				const token = await generateToken();
				set({ token, error: null });
			} catch (e) {
				set({
					error: e instanceof Error ? e.message : "Unknown error",
				});
			}
		},
	};
});
