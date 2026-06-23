import type { Connection, Drone, Hub } from "../../types/simulation"
import DetailPanel, { DetailRow } from "./DetailPanel"

interface ConnectionDetailPanelProps {
	connection: Connection
	hubs: Map<string, Hub>
	drones: Map<string, Drone>
	onClose: () => void
}

export default function ConnectionDetailPanel({
	connection,
	hubs,
	drones,
	onClose,
}: ConnectionDetailPanelProps) {
	const [a, b] = connection.hubs
	let activeDrones = 0
	for (const d of drones.values()) {
		const onLink =
			(d.location === a && d.destination === b) ||
			(d.location === b && d.destination === a)
		if (onLink) activeDrones++
	}

	return (
		<DetailPanel
			title='Connection'
			onClose={onClose}
			position='right-4 top-4'>
			<DetailRow
				label='From:'
				value={hubs.get(a)?.name ?? "Unknown"}
			/>
			<DetailRow
				label='To:'
				value={hubs.get(b)?.name ?? "Unknown"}
			/>
			<DetailRow
				label='Capacity:'
				value={connection.capacity}
			/>
			<DetailRow
				label='Active Drones:'
				value={activeDrones}
			/>
		</DetailPanel>
	)
}
