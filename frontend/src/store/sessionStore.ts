import { create } from "zustand"
import { generateToken } from "../services/api"
import type { Token } from "../types/api"

interface SessionStore {
	token: Token | null
	isLoading: boolean
	isOffline: boolean
	error: string | null
	setError: (error: string | null) => void
	setIsLoading: (isLoading: boolean) => void
	fetchToken: () => Promise<void>
}

export const useSessionStore = create<SessionStore>(set => ({
	token: null,
	isLoading: false,
	isOffline: false,
	error: null,

	setError: (error: string | null) => set({ error }),
	setIsLoading: (isLoading: boolean) => set({ isLoading }),
	fetchToken: async () => {
		try {
			const token = await generateToken()
			set({ token, error: null, isOffline: false })
		} catch (e) {
			// TypeError means fetch itself failed — backend unreachable
			if (e instanceof TypeError) {
				set({ isOffline: true, error: null })
			} else {
				set({
					error: e instanceof Error ? e.message : "Unknown error",
					isOffline: false,
				})
			}
		}
	},
}))
