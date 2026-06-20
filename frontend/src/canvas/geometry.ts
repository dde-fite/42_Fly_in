// ── Uniform camera model ────────────────────────────────────────────────────
// Everything the canvas draws is sized in *model units* and multiplied by the
// view `scale` exactly once, at draw time. There are no pixel floors or ceilings
// anywhere, so the whole scene is a single rigid object the camera zooms in and
// out of: zooming is perfectly proportional and reversible. Hub positions live
// on an integer grid (neighbours are 1 unit apart), so these constants are
// fractions of that grid cell.
const WORLD = {
	connTrackSpacing: 0.09, // gap between parallel tracks on a connection
	stationTrackSpacing: 0.22, // gap between platform tracks inside a station
	railWidth: 0.03, // rail stroke width
	fontSize: 0.14, // station name height
	platformH: 0.05, // height of each platform band
	platformGap: 0.022, // gap between platform and track area
	droneSize: 0.09, // drone glyph radius-ish
	charWidth: 0.1, // box width contributed per name character
	boxPadX: 0.18, // horizontal box padding
	minBoxWidth: 0.34, // smallest station box width
} as const

// Rail spacing/width for connection tracks (pure functions of scale).
export function railMetrics(scale: number) {
	return {
		trackSpacing: scale * WORLD.connTrackSpacing,
		railWidth: scale * WORLD.railWidth,
	}
}

// Pixel size of a drone glyph at this scale.
export function droneSizeFor(scale: number) {
	return scale * WORLD.droneSize
}

export function getHubBox(name: string, scale: number, capacity = 1) {
	const fontSize = scale * WORLD.fontSize
	const platformH = scale * WORLD.platformH
	const platformGap = scale * WORLD.platformGap
	const trackSpacing = scale * WORLD.connTrackSpacing
	const stationTrackSpacing = scale * WORLD.stationTrackSpacing
	const innerH = stationTrackSpacing * Math.max(1, capacity)
	const boxH = innerH + (platformH + platformGap) * 2
	const boxW =
		scale *
		Math.max(WORLD.minBoxWidth, WORLD.charWidth * name.length + WORLD.boxPadX)
	return {
		boxW,
		boxH,
		fontSize,
		trackSpacing,
		stationTrackSpacing,
		platformH,
		platformGap,
		innerH,
	}
}
