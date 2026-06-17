import type { Hub } from "../../types/simulation"
import {
	closeButton,
	detailHeader,
	detailLabel,
	detailPanel,
	detailRow,
	detailValue,
} from "./panelStyles"

interface HubDetailPanelProps {
	hub: Hub
	onClose: () => void
}

export default function HubDetailPanel({ hub, onClose }: HubDetailPanelProps) {
	return (
		<div className={`${detailPanel} right-4 top-4`}>
			<div className={detailHeader}>
				<h4 className='m-0 text-white text-[0.95rem] tracking-wide'>
					{hub.name}
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
					<span className={detailLabel}>Position:</span>
					<strong className={detailValue}>{hub.position.join(", ")}</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Access:</span>
					<strong className={detailValue}>{hub.access}</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Capacity:</span>
					<strong className={detailValue}>{hub.capacity}</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Drones:</span>
					<strong className={detailValue}>{hub.drones.length}</strong>
				</div>
				<div className={detailRow}>
					<span className={detailLabel}>Connections:</span>
					<strong className={detailValue}>{hub.connections.length}</strong>
				</div>
			</div>
		</div>
	)
}
