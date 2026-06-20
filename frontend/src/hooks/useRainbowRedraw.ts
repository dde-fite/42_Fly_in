import { useEffect, useMemo } from "react";
import { isRainbow } from "../canvas/palette";
import type { Hub } from "../types/simulation";

// While any station uses the animated "rainbow" colour, redraw every frame so
// its hue cycles. With no rainbow station the canvas stays static (no loop).
export function useRainbowRedraw(hubs: Map<string, Hub>, redraw: () => void) {
	const hasRainbow = useMemo(
		() => Array.from(hubs.values()).some((h) => isRainbow(h.color)),
		[hubs],
	);
	useEffect(() => {
		if (!hasRainbow) return;
		let raf = requestAnimationFrame(function tick() {
			redraw();
			raf = requestAnimationFrame(tick);
		});
		return () => cancelAnimationFrame(raf);
	}, [hasRainbow, redraw]);
}
