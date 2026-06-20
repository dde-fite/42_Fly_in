import type { Hub } from "../types/simulation"
import { getHubBox } from "./geometry"
import { modelToCanvas, type View } from "./view"

type HubBox = ReturnType<typeof getHubBox>

// Canvas Y of station track `t` (centre line), given the box centre Y.
export function stationTrackY(centerY: number, box: HubBox, t: number): number {
	const top = centerY - box.boxH / 2 + box.platformH + box.platformGap
	return top + (t + 0.5) * box.stationTrackSpacing
}

// Centre a connection's tracks within each station's larger track set, so a
// connection track joins the same relative platform row at both ends.
export function trackOffsets(capA: number, capB: number, connCap: number) {
	return {
		offA: Math.floor((capA - connCap) / 2),
		offB: Math.floor((capB - connCap) / 2),
	}
}

const clampTrack = (t: number, cap: number) => Math.max(0, Math.min(cap - 1, t))

export interface Point {
	x: number
	y: number
}

// Endpoints (canvas) of the connection track joining station track `tA` of
// `hubA` to station track `tB` of `hubB`. Each station exits on the side that
// faces the other; the lines start at the box edge and the station body (drawn
// afterwards) tucks the roots.
export function connectionTrackLine(
	view: View,
	hubA: Hub,
	hubB: Hub,
	tA: number,
	tB: number,
): [Point, Point] {
	const [x1, y1] = modelToCanvas(view, ...hubA.position)
	const [x2, y2] = modelToCanvas(view, ...hubB.position)
	const bA = getHubBox(hubA.name, view.scale, hubA.capacity)
	const bB = getHubBox(hubB.name, view.scale, hubB.capacity)
	const dir = x2 >= x1 ? 1 : -1
	const edgeA = x1 + dir * (bA.boxW / 2)
	const edgeB = x2 - dir * (bB.boxW / 2)
	return [
		{ x: edgeA, y: stationTrackY(y1, bA, clampTrack(tA, hubA.capacity)) },
		{ x: edgeB, y: stationTrackY(y2, bB, clampTrack(tB, hubB.capacity)) },
	]
}
