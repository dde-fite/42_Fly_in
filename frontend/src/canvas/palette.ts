// Canvas colour palette, styled like SimSig / railway CTC panels: white tracks,
// red occupied tracks, amber/yellow text for information (station names, track
// numbers, counts). A hub may override its identity colour via the backend.

// Tracks ("vias")
export const TRACK = "#ffffff" // clear track
export const TRACK_OCCUPIED = "#ff1744" // occupied by a drone
export const TRACK_SELECTED = "#ffee58" // selected connection
export const TRACK_CASING = "#0a0a0a" // dark casing under a track block
export const TRACK_PRIORITY = "#00e676" // leads to a priority hub
export const TRACK_BLOCKED = "#d50000" // leads to a blocked hub

// CTC chrome
export const INFO = "#ffd54f" // amber text: names, track numbers, counts
export const STRUCTURE = "#cfd8dc" // light grey outlines for plain stations
export const PANEL_BG = "#0d0d0d" // station body background
export const PLATFORM_BG = "#1a1a1a" // platform (anden) fill

// Semantic hub markers
export const ORIGIN = "#00e676"
export const DEST = "#ff1744"

// Resolve a hub's backend colour to a canvas fill. Plain hex strings are used as
// is; the special "rainbow" value animates through the hue wheel over time;
// a hub with no colour falls back to the amber info colour.
export function resolveHubColor(color: string | undefined): string {
	if (!color) return INFO
	if (color.toLowerCase() === "rainbow") return rainbowColor()
	return color
}

// True when a hub uses the animated rainbow colour (drives continuous redraw).
export function isRainbow(color: string | undefined): boolean {
	return color?.toLowerCase() === "rainbow"
}

// Time-animated rainbow colour: a full hue cycle every ~7.2s.
export function rainbowColor(): string {
	const hue = (performance.now() / 20) % 360
	return `hsl(${hue}, 90%, 55%)`
}

// Time-animated rainbow palette: `count` hues evenly spread around the wheel,
// all rotating together. Lets a station show several rainbow colours at once.
export function rainbowColors(count = 3): string[] {
	const base = (performance.now() / 20) % 360
	return Array.from(
		{ length: count },
		(_, i) => `hsl(${(base + (i * 360) / count) % 360}, 90%, 55%)`,
	)
}
