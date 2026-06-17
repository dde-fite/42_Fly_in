import type { Connection, Drone, Hub } from "../../types/simulation"
import {
	closeButton,
	detailHeader,
	detailLabel,
	detailPanel,
	detailRow,
	detailValue,
} from "./panelStyles"

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
	const activeDrones = Array.from(drones.values()).filter(
		d =>
			(d.location === connection.hubs[0] &&
				d.destination === connection.hubs[1]) ||
			(d.location === connection.hubs[1] &&
				d.destination === connection.hubs[0]),
	).length

	return (
		<div className={`${detailPanel} right-4 top-50`}>
			<div className={detailHeader}>
				<h4 className='m-0 text-white text-[0.95rem] tracking-wide'>
					Connection
				</h4>
				<button
					className={closeButton}
					onClick={onClose}
					type='button'>
					✕
				</button>
			</div>
			<div className='p-3'>
				<div className={detailRow}>
					<span className={detailLabel}>From:</span>
					<strong className={detailValue}>
						{hubs.get(connection.hubs[0])?.name ?? "Unknown"}
					</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>To:</span>
					<strong className={detailValue}>
						{hubs.get(connection.hubs[1])?.name ?? "Unknown"}
					</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Capacity:</span>
					<strong className={detailValue}>{connection.capacity}</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Active Drones:</span>
					<strong className={detailValue}>{activeDrones}</strong>
				</div>
			</div>
		</div>
	)
}
