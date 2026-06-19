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
	const isRainbow = hub.color?.toLowerCase() === "rainbow"
	// Header colour follows the station: its API colour (rainbow animates), or the
	// shared darker header-purple gradient when no colour is specified.
	const headerClass = isRainbow
		? "px-3 py-3 flex justify-between items-center border-b border-black/40 rainbow-bg"
		: detailHeader
	const headerStyle =
		hub.color && !isRainbow
			? { background: `linear-gradient(135deg, ${hub.color}, #000)` }
			: undefined
	const panelStyle =
		hub.color && !isRainbow ? { borderColor: hub.color } : undefined

	return (
		<div
			className={`${detailPanel} right-4 top-4`}
			style={panelStyle}>
			<div
				className={headerClass}
				style={headerStyle}>
				<h4 className='m-0 text-white text-[0.95rem] tracking-wide drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]'>
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
				{hub.color && (
					<div className={detailRow}>
						<span className={detailLabel}>Color:</span>
						<span className='flex items-center gap-2'>
							<strong className={detailValue}>{hub.color}</strong>
							<span
								className={`inline-block w-4 h-4 rounded-sm border border-white/30 ${
									hub.color.toLowerCase() === "rainbow" ? "rainbow-swatch" : ""
								}`}
								style={
									hub.color.toLowerCase() === "rainbow"
										? undefined
										: { backgroundColor: hub.color }
								}
							/>
						</span>
					</div>
				)}
			</div>
		</div>
	)
}
