import { type MutableRefObject, useCallback, useEffect, useRef } from "react"
import { computeDroneMoves, type DroneMoveBase } from "../canvas/moves"
import type { DroneMove } from "../canvas/scene"
import type { Connection, Hub, Simulation } from "../types/simulation"
import { GLIDE_RATIO, TURN_DELAY } from "./usePlayback"

interface Options {
	simulation: Simulation
	// Store turn counter. A glide plays only on a single forward step
	// (turn === prevTurn + 1); restarts (reset to 0) and multi-step jumps skip it.
	turn: number
	hubs: Map<string, Hub>
	connections: Map<string, Connection>
	// Latest playback multiplier (a ref so the loop reads it without restarting).
	playbackSpeedRef: MutableRefObject<number>
	// Frame map the renderer reads; this hook writes eased progress into it.
	movesRef: MutableRefObject<Map<string, DroneMove> | null>
	redraw: () => void
}

// Drives the drone-move glide. On each real turn change it diffs the simulation
// (computeDroneMoves), then animates eased progress 0 → 1 into `movesRef`,
// redrawing every frame. The glide duration shrinks with playback speed so it
// always finishes before the next turn's state arrives.
export function useDroneAnimation({
	simulation,
	turn,
	hubs,
	connections,
	playbackSpeedRef,
	movesRef,
	redraw,
}: Options) {
	const rafRef = useRef<number | null>(null)
	const prevSimRef = useRef<Simulation | null>(null)
	const prevTurnRef = useRef<number>(turn)

	const cancel = useCallback(() => {
		if (rafRef.current !== null) {
			cancelAnimationFrame(rafRef.current)
			rafRef.current = null
		}
		if (movesRef.current !== null) {
			movesRef.current = null
			redraw()
		}
	}, [movesRef, redraw])

	const runAnimation = useCallback(
		(base: DroneMoveBase[]) => {
			if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
			if (base.length === 0) {
				movesRef.current = null
				redraw()
				return
			}
			// Glide for a fixed fraction (GLIDE_RATIO) of the current turn so it
			// always finishes before the next turn's state arrives. Progress is
			// accumulated per frame against the *live* speed, so changing playback
			// speed mid-glide takes effect immediately and the duration stays tied
			// to TURN_DELAY instead of a magic constant.
			const ease = (t: number) => t * t * (3 - 2 * t)
			let progressRaw = 0
			let last = performance.now()
			const tick = (now: number) => {
				const speed =
					playbackSpeedRef.current > 0 ? playbackSpeedRef.current : 1
				const duration = (TURN_DELAY * GLIDE_RATIO) / speed
				progressRaw = Math.min(1, progressRaw + (now - last) / duration)
				last = now
				const progress = ease(progressRaw)
				const frame = new Map<string, DroneMove>()
				for (const b of base) {
					frame.set(b.id, { segments: b.segments, progress })
				}
				movesRef.current = frame
				redraw()
				if (progressRaw < 1) {
					rafRef.current = requestAnimationFrame(tick)
				} else {
					movesRef.current = null
					rafRef.current = null
					redraw()
				}
			}
			rafRef.current = requestAnimationFrame(tick)
		},
		[movesRef, playbackSpeedRef, redraw],
	)

	// Animate the hub transitions on each single forward turn. A reset (turn back
	// to 0 on a new/replaced map) or a multi-step jump (advance N) is not a glide:
	// cancel any in-flight animation and snap to the new state instead of playing
	// a phantom move across unrelated states.
	useEffect(() => {
		const prev = prevSimRef.current
		const prevTurn = prevTurnRef.current
		prevSimRef.current = simulation
		prevTurnRef.current = turn
		if (!prev || turn !== prevTurn + 1) {
			cancel()
			return
		}
		const base = computeDroneMoves(prev, simulation, hubs, connections)
		if (base.length > 0) runAnimation(base)
	}, [simulation, turn, hubs, connections, runAnimation, cancel])

	useEffect(
		() => () => {
			if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
		},
		[],
	)
}
