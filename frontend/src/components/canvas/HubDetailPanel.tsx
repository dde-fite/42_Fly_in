import type { Hub } from "../../types/simulation";
import DetailPanel, { DetailRow } from "./DetailPanel";
import { detailLabel, detailRow, detailValue } from "./panelStyles";

interface HubDetailPanelProps {
	hub: Hub;
	onClose: () => void;
}

export default function HubDetailPanel({ hub, onClose }: HubDetailPanelProps) {
	const isRainbow = hub.color?.toLowerCase() === "rainbow";
	// Solid colour to theme the panel with, or undefined for the default purple
	// header / rainbow animation.
	const color = hub.color && !isRainbow ? hub.color : undefined;

	return (
		<DetailPanel
			title={hub.name}
			onClose={onClose}
			position="right-4 top-4"
			panelStyle={color ? { borderColor: color } : undefined}
			headerClassName={
				isRainbow
					? "px-3 py-3 flex justify-between items-center border-b border-black/40 rainbow-bg"
					: undefined
			}
			headerStyle={
				color
					? { background: `linear-gradient(135deg, ${color}, #000)` }
					: undefined
			}
			titleClassName="drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]"
		>
			<DetailRow label="Position:" value={hub.position.join(", ")} />
			<DetailRow label="Access:" value={hub.access} />
			<DetailRow label="Capacity:" value={hub.capacity} />
			<DetailRow label="Drones:" value={hub.drones.length} />
			<DetailRow label="Connections:" value={hub.connections.length} />
			{hub.color && (
				<div className={detailRow}>
					<span className={detailLabel}>Color:</span>
					<span className="flex items-center gap-2">
						<strong className={detailValue}>{hub.color}</strong>
						<span
							className={`inline-block w-4 h-4 rounded-sm border border-white/30 ${
								isRainbow ? "rainbow-swatch" : ""
							}`}
							style={color ? { backgroundColor: color } : undefined}
						/>
					</span>
				</div>
			)}
		</DetailPanel>
	);
}
