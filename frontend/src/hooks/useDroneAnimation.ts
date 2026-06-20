import { type MutableRefObject, useCallback, useEffect, useRef } from "react";
import { computeDroneMoves, type DroneMoveBase } from "../canvas/moves";
import type { DroneMove } from "../canvas/scene";
import type { Connection, Hub, Simulation } from "../types/simulation";

interface Options {
	simulation: Simulation;
	hubs: Map<string, Hub>;
	connections: Map<string, Connection>;
	// Latest playback multiplier (a ref so the loop reads it without restarting).
	playbackSpeedRef: MutableRefObject<number>;
	// Frame map the renderer reads; this hook writes eased progress into it.
	movesRef: MutableRefObject<Map<string, DroneMove> | null>;
	redraw: () => void;
}

// Drives the drone-move glide. On each real turn change it diffs the simulation
// (computeDroneMoves), then animates eased progress 0 → 1 into `movesRef`,
// redrawing every frame. The glide duration shrinks with playback speed so it
// always finishes before the next turn's state arrives.
export function useDroneAnimation({
	simulation,
	hubs,
	connections,
	playbackSpeedRef,
	movesRef,
	redraw,
}: Options) {
	const rafRef = useRef<number | null>(null);
	const prevSimRef = useRef<Simulation | null>(null);

	const runAnimation = useCallback(
		(base: DroneMoveBase[]) => {
			if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
			if (base.length === 0) {
				movesRef.current = null;
				redraw();
				return;
			}
			// Full glide on normal play; divided by the multiplier on fast play.
			// Stays under TURN_DELAY (1000ms) so it always completes before the
			// next turn's state arrives.
			const speed = playbackSpeedRef.current > 0 ? playbackSpeedRef.current : 1;
			const duration = 800 / speed;
			const start = performance.now();
			const ease = (t: number) => t * t * (3 - 2 * t);
			const tick = (now: number) => {
				const raw = Math.min(1, (now - start) / duration);
				const progress = ease(raw);
				const frame = new Map<string, DroneMove>();
				for (const b of base) {
					frame.set(b.id, {
						fromId: b.fromId,
						toId: b.toId,
						tA: b.tA,
						tB: b.tB,
						progress,
					});
				}
				movesRef.current = frame;
				redraw();
				if (raw < 1) {
					rafRef.current = requestAnimationFrame(tick);
				} else {
					movesRef.current = null;
					rafRef.current = null;
					redraw();
				}
			};
			rafRef.current = requestAnimationFrame(tick);
		},
		[movesRef, playbackSpeedRef, redraw],
	);

	// Detect drones that changed hubs between the previous and current state and
	// animate the transition. Only a real turn change triggers it: re-runs from
	// other deps must not cancel an in-flight glide.
	useEffect(() => {
		const prev = prevSimRef.current;
		if (prev === simulation) return;
		prevSimRef.current = simulation;
		if (!prev) return;
		const base = computeDroneMoves(prev, simulation, hubs, connections);
		if (base.length > 0) runAnimation(base);
	}, [simulation, hubs, connections, runAnimation]);

	useEffect(
		() => () => {
			if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
		},
		[],
	);
}
