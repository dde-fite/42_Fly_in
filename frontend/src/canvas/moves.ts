import type { Connection, Hub, Simulation } from "../types/simulation"
import type { DroneMove, MoveSegment } from "./scene"
import { trackOffsets } from "./track"

// A drone move before easing: the same shape as DroneMove minus the animated
// `progress`, plus the drone `id` so the animation can key frames by drone.
export type DroneMoveBase = Omit<DroneMove, "progress"> & { id: string }

// One graph edge: the connection joining two hubs, with its capacity.
interface Edge {
	connId: string
	to: string
	capacity: number
}

// A drone that changed hubs this turn, with the hub path connecting its old and
// new location (length 2 for a direct neighbour, longer when it crossed several
// zero-cost zones in a single turn). Track rows are assigned afterwards.
interface RawMove {
	id: string
	hubPath: string[]
	edges: Edge[]
}

// Adjacency list keyed by hub id. Neighbours are sorted by connection id so the
// shortest-path search is deterministic across turns.
function buildGraph(connections: Map<string, Connection>): Map<string, Edge[]> {
	const graph = new Map<string, Edge[]>()
	const add = (from: string, edge: Edge) => {
		const list = graph.get(from)
		if (list) list.push(edge)
		else graph.set(from, [edge])
	}
	for (const [connId, c] of connections) {
		const [h0, h1] = c.hubs
		add(h0, { connId, to: h1, capacity: c.capacity })
		add(h1, { connId, to: h0, capacity: c.capacity })
	}
	for (const list of graph.values())
		list.sort((a, b) => a.connId.localeCompare(b.connId))
	return graph
}

// Shortest hub path from `start` to `goal` over the connection graph, returned
// as the edges traversed. Empty when the two hubs are unreachable. BFS so the
// glide takes the fewest hops, matching how the backend advances a drone.
function findPath(
	graph: Map<string, Edge[]>,
	start: string,
	goal: string,
): Edge[] {
	if (start === goal) return []
	const cameFrom = new Map<string, { prev: string; edge: Edge }>()
	const queue: string[] = [start]
	const seen = new Set<string>([start])
	while (queue.length > 0) {
		const current = queue.shift() as string
		for (const edge of graph.get(current) ?? []) {
			if (seen.has(edge.to)) continue
			seen.add(edge.to)
			cameFrom.set(edge.to, { prev: current, edge })
			if (edge.to === goal) {
				const edges: Edge[] = []
				let node = goal
				while (node !== start) {
					const step = cameFrom.get(node)
					if (!step) return []
					edges.unshift(step.edge)
					node = step.prev
				}
				return edges
			}
			queue.push(edge.to)
		}
	}
	return []
}

// Compare the previous and current simulation and return one entry per drone
// that changed hubs. Each leg of a move is assigned its own track row on its
// connection (drones sharing a connection stack on rows 0, 1, 2 …) centred
// within both stations via `trackOffsets`.
export function computeDroneMoves(
	prev: Simulation,
	next: Simulation,
	hubs: Map<string, Hub>,
	connections: Map<string, Connection>,
): DroneMoveBase[] {
	const graph = buildGraph(connections)
	const raws: RawMove[] = []

	for (const [id, drone] of Object.entries(next.drones)) {
		const old = prev.drones[id]
		if (!old || old.location === drone.location) continue
		if (!hubs.has(old.location) || !hubs.has(drone.location)) continue

		// Resolve the hub path even when the two hubs are not direct neighbours,
		// so a long move glides through the intermediate hubs instead of jumping.
		const edges = findPath(graph, old.location, drone.location)
		if (edges.length === 0) continue

		const hubPath = [old.location]
		for (const edge of edges) hubPath.push(edge.to)
		raws.push({ id, hubPath, edges })
	}

	// Deterministic ordering by drone id so track rows are stable across turns
	// and don't reshuffle with object iteration order.
	raws.sort((a, b) => a.id.localeCompare(b.id))

	const base: DroneMoveBase[] = []
	// Rows are handed out per connection, so two drones crossing the same
	// connection (either direction) never share a row mid-glide.
	const perConn = new Map<string, number>()
	for (const r of raws) {
		const segments: MoveSegment[] = []
		for (let i = 0; i < r.edges.length; i++) {
			const edge = r.edges[i]
			const fromId = r.hubPath[i]
			const toId = r.hubPath[i + 1]
			const capFrom = hubs.get(fromId)?.capacity ?? 1
			const capTo = hubs.get(toId)?.capacity ?? 1
			const t = perConn.get(edge.connId) ?? 0
			perConn.set(edge.connId, t + 1)
			const { offA, offB } = trackOffsets(capFrom, capTo, edge.capacity)
			segments.push({ fromId, toId, tA: offA + t, tB: offB + t })
		}
		base.push({ id: r.id, segments })
	}

	return base
}
