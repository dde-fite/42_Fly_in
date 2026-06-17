import { useEffect, useState } from "react"
import { useSessionStore } from "../store/sessionStore"

export enum Player {
	PAUSE = "pause",
	PLAY = "play",
	FAST = "fast",
}

const TURN_DELAY = 1000

const MULTIPLIER: Record<Player, number> = {
	[Player.PAUSE]: 0,
	[Player.PLAY]: 1,
	[Player.FAST]: 3,
}

// Owns playback state and the auto-advance loop. Pauses when there is no
// simulation; advances one turn every TURN_DELAY / multiplier ms while playing.
export function usePlayback(
	hasSimulation: boolean,
	advanceSimulation: (steps: number) => void,
) {
	const [player, setPlayer] = useState<Player>(Player.PAUSE)
	const isLoading = useSessionStore(state => state.isLoading)

	// Pause when simulation is cleared
	useEffect(() => {
		if (!hasSimulation) setPlayer(Player.PAUSE)
	}, [hasSimulation])

	// Auto-advance loop
	useEffect(() => {
		if (player === Player.PAUSE || isLoading || !hasSimulation) return
		const delay = TURN_DELAY / MULTIPLIER[player]
		const t = setTimeout(() => advanceSimulation(1), delay)
		return () => clearTimeout(t)
	}, [player, isLoading, hasSimulation, advanceSimulation])

	const togglePlay = () =>
		setPlayer(p => (p === Player.PAUSE ? Player.PLAY : Player.PAUSE))

	return { player, setPlayer, togglePlay }
}
